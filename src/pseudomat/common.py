import base64
import hashlib
import json
import re
import typing as T

from aiohttp import web_exceptions as web
from jwcrypto import jwk, jws

VERSION = '0.1.0'
EMAIL_REGEX_FULLMATCH = r'[-\w\.]+@(?:[-\w]+\.)+[a-z]+'


def urlsafe_b64encode_np(payload: bytes) -> str:
    """
    Padding stripping version of `base64.urlsafe_b64encode()` as described in
    Appendix C of :rfc:`7515`.
    """
    encode = base64.urlsafe_b64encode(payload)
    return encode.decode('utf-8').rstrip('=')


def urlsafe_b64decode(payload: str) -> bytes:
    """
    Non-padding version of `base64.urlsafe_b64decode()` as described in Appendix
    C of :rfc:`7515`.
    """
    size = len(payload) % 4
    if size == 2:
        payload += '=='
    elif size == 3:
        payload += '='
    elif size != 0:
        raise ValueError('Invalid base64 string')
    return base64.urlsafe_b64decode(payload.encode('utf-8'))


def urlsafe_digest(o: T.Union[str, list, dict]) -> str:
    """
    A 43-character url-safe digest.

    This function:

    -   makes a canonical json serialization of parameter `o`
    -   computes the SHA256 digest (32 bytes)
    -   returns the urlsafe base64 encoding (44 bytes) as a string

    Parameters:
        o: anything json-serializable
    """
    return urlsafe_b64encode_np(
        hashlib.sha256(
            json_canonical_encode(o).encode('utf-8')
        ).digest()
    )


def json_canonical_encode(o: T.Union[str, list, dict]) -> str:
    return json.dumps(o, separators=(',', ':'), sort_keys=True)


def with_kid(key: jwk.JWK):
    key_id = key.thumbprint()
    key = json.loads(key.export())
    key['kid'] = key_id
    return jwk.JWK.from_json(json_canonical_encode(key))


def project_id(email: str, name: str) -> str:
    """
    A 43-character url-safe project ID.
    """
    return urlsafe_digest([email, name])


def validate_project_jws(project_jws) -> T.Dict[str, str]:

    # Validate outer semantics: dot separated base64url_encoded:
    if not re.fullmatch(r'[-\w]+\.[-\w]+\.[-\w]+', project_jws):
        raise web.HTTPBadRequest(
            reason="Syntax error in JWS"
        )

    # Attempt decoding the JWS:
    decoder = jws.JWS()
    try:
        decoder.deserialize(project_jws)
    except jws.InvalidJWSObject:
        raise web.HTTPBadRequest(
            reason="Syntax error in JWS"
        )

    # From here on, "Unprocessable Entity" must be raised on error:
    try:
        # Assert kid is in jose header:
        kid = decoder.jose_header.get('kid', None)
        assert kid is not None, "No 'kid' entry in jose header."

        # Assert payload is a JWKS, and extract the keys:
        try:
            jwks = jwk.JWKSet.from_json(decoder.objects['payload'])
        except jwk.InvalidJWKValue:
            raise web.HTTPUnprocessableEntity(
                reason="Payload is not a valid JWKS."
            )

        # Assert JWKS contains one signing and one encryption key, of the right
        # type:
        uses = {'sig': [], 'enc': []}
        for key in jwks['keys']:  # type: jwk.JWK
            assert key.key_type == 'EC' and key.key_curve == 'P-384', \
                "Invalid key type in keyset."
            assert not key.has_private, "Private key found in keyset."
            # noinspection PyProtectedMember
            use = key._params.get('use', '(missing)')
            assert use in uses, "Invalid 'use' claim: %s" % use
            uses[use].append(key.export())
        assert len(uses['sig']) == 1 and len(uses['enc']) == 1, \
            "Keyset doesn’t contain exactly one signing key and one encryption key."

        # Assert kid is among the extracted keys:
        signing_key = jwks.get_key(kid)
        assert signing_key is not None, "Payload is not self-signed."

        # Validate the signature:
        try:
            decoder.verify(signing_key)
        except jws.InvalidJWSSignature:
            raise web.HTTPUnprocessableEntity(
                reason="Signature validation failed."
            )

        # Decode the payload. This is not in a try-except block, because we've
        # already asserted that the payload is a valid JWKS.
        payload = json.loads(decoder.payload)
        expected_claims = {'iat', 'iss', 'jti', 'keys', 'sub'}
        for claim in expected_claims:
            assert claim in payload, "Required claim '%s' is missing." % claim
        for claim in payload.keys():
            assert claim in expected_claims, "Claim '%s' is unexpected." % claim

        # Assert 'iss' value is an e-mail address:
        email = payload['iss']
        assert email is not None, "Missing required 'iss' claim."
        assert re.fullmatch(EMAIL_REGEX_FULLMATCH, email), \
            "%s is not a valid e-mail address." % email

        # Assert 'sub' value is well-formed:
        name = payload['sub']
        assert name is not None and len(name) > 0, "Required 'sub' claim is missing."
        assert len(name) <= 80, "Claim 'sub' length exceeds 80 characters."
        assert not any(ord(c) < 32 for c in name), "Illegal control characters in claim 'sub'."

        # Assert 'jti' value is correct:
        jti = payload['jti']
        assert jti is not None, "Missing required 'jti' claim."
        assert project_id(email, name) == jti, "jti '%s' doesn’t compute." % jti

    except web.HTTPUnprocessableEntity:
        raise
    except AssertionError as e:
        raise web.HTTPUnprocessableEntity(
            reason=str(e)
        )

    return {
        'project_id': jti,
        'email': email,
        'name': name,
        'sig_key': uses['sig'][0],
        'enc_key': uses['enc'][0]
    }
