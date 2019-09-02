import base64
import binascii
import hashlib
import json
import logging
import typing as T

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature
from jwcrypto import jwk, jws

from . import schemas

_logger = logging.getLogger(__package__)
VERSION = '0.1.0'
SIGNING_ALGORITHM = 'EdDSA'


def b64encode(b: bytes, rtype=str) -> T.Union[str, bytes]:
    retval = base64.urlsafe_b64encode(b).rstrip(b'=')
    if rtype == str:
        retval = retval.decode('ascii')
    return retval


def b64decode(s: T.Union[str, bytes]) -> bytes:
    if isinstance(s, str):
        s = s.encode('ascii')
    length = len(s) % 4
    if length == 1:
        # Same exception as raised by base64.urlsafe_b64decode():
        raise binascii.Error()
    elif length == 2:
        s += b'=='
    elif length == 3:
        s += b'='
    return base64.urlsafe_b64decode(s)


def json_dumps(o: T.Union[str, list, dict]) -> str:
    return json.dumps(o, separators=(',', ':'), sort_keys=True)


json_loads = json.loads


def fingerprint(o: T.Union[bytes, str, list, dict], rtype=str) -> T.Union[str, bytes]:
    if isinstance(o, list) or isinstance(o, dict):
        o = json_dumps(o)
    if isinstance(o, str):
        o = o.encode('utf-8')
    return b64encode(
        hashlib.sha256(o).digest()[:24],
        rtype=rtype
    )


def validate_jws(data: str, typ: str) -> T.Tuple[jws.JWS, T.Dict[str, T.Any]]:
    # Attempt decoding the JWS:
    decoder = jws.JWS()
    try:
        decoder.deserialize(data)
    except jws.InvalidJWSObject:
        raise ValueError(
            "Syntax error in JWS"
        )
    if decoder.jose_header.get('typ', None) != typ:
        raise ValueError("Invalid 'typ' claim.")
    try:
        payload = json_loads(decoder.objects['payload'])
    except json.JSONDecodeError:
        raise ValueError(
            "Payload isn’t valid JSON"
        )

    return decoder, payload


def validate_project_jws(data: str) -> dict:
    # JOSE header checks:
    # # Assert 'kid' is in jose header:
    # kid = decoder.jose_header.get('kid', None)
    # assert kid is not None, "No 'kid' entry in jose header."

    decoder, payload = validate_jws(data, 'project')

    # From here on, "Unprocessable Entity" must be raised on error:
    try:
        schemas.validate_schema(payload, 'project')
        assert payload['sub'] == payload['sub'].strip(' '), \
            "Claim 'sub' mustn’t start or end with whitespace."
        assert payload['jti'] == fingerprint(payload['sub']), \
            "Claim 'jti' doesn’t correspond with claim 'sub'."

        # Extract and syntax-check the keys:
        signing_key: T.Optional[jwk.JWK] = None
        for claim in ('psig', 'penc'):
            value = payload[claim]
            try:
                key = jwk.JWK.from_json(json_dumps(value))
            except jwk.JWException:
                raise web.HTTPUnprocessableEntity(
                    text="Claim '%s' doesn’t contain a valid JWK."
                )
            assert not key.has_private, "Private key found in keyset."
            if claim == 'psig':
                signing_key = key

        # Validate the signature:
        try:
            decoder.verify(signing_key, alg='EdDSA')
        except jws.InvalidJWSSignature:
            raise web.HTTPUnprocessableEntity(
                text="Signature validation failed."
            )

    except AssertionError as e:
        raise web.HTTPUnprocessableEntity(
            text=str(e)
        )

    return payload


def validate_invite_jws(data: str, project_key: jwk.JWK) -> dict:
    """
    Raises:
        ValueError: Corresponds to
    """
    decoder, payload = validate_jws(data, 'pinvite')

    # From here on, "Unprocessable Entity" must be raised on error:
    try:
        schemas.validate_schema(payload, 'pinvite')
        assert payload['sub'] == payload['sub'].strip(' '), \
            "Claim 'sub' mustn’t start or end with whitespace."
        assert payload['jti'] == fingerprint([payload['iss'], payload['sub']]), \
            "Claim 'jti' doesn’t compute."

        # Extract and syntax-check the keys:
        for claim in ('psig', 'penc'):
            value = payload[claim]
            try:
                key = jwk.JWK.from_json(json_dumps(value))
            except jwk.JWException:
                raise web.HTTPUnprocessableEntity(
                    text="Claim '%s' doesn’t contain a valid JWK."
                )
            assert not key.has_private, "Private key found in keyset."

        # Validate the signature:
        try:
            decoder.verify(project_key, alg='EdDSA')
        except jws.InvalidJWSSignature:
            raise web.HTTPUnprocessableEntity(
                text="Signature validation failed."
            )

    except AssertionError as e:
        raise web.HTTPUnprocessableEntity(
            text=str(e)
        )

    return payload


class SignedObject(object):

    def __init__(self, s: str):
        try:
            objects = s.split('.')
            assert len(objects) == 3
            self.signee = '.'.join([objects[0], objects[1]]).encode('ascii')
            self.header = json_loads(b64decode(objects[0]).decode('utf-8'))
            self.payload = json_loads(b64decode(objects[1]).decode('utf-8'))
            self.signature = b64decode(objects[2])
        except Exception as e:
            raise ValueError('Syntax error in signed object: %s' % s) from e

    def validate(self, key: T.Optional[Ed25519PublicKey]):
        assert self.header.get('alg', None) == SIGNING_ALGORITHM
        if key is None:
            try:
                key = Ed25519PublicKey.from_public_bytes(b64decode(self.payload['psig']))
            except Exception:
                raise InvalidSignature()
        key.verify(self.signature, self.signee)

    @staticmethod
    def create(o: dict, k: Ed25519PrivateKey, typ: str) -> str:
        header = b64encode(json_dumps({'typ': typ, 'alg': SIGNING_ALGORITHM}).encode('utf-8'))
        payload = b64encode(json_dumps(o).encode('utf-8'))
        signee = header + '.' + payload
        signature = k.sign(signee.encode('ascii'))
        return signee + '.' + b64encode(signature)


def delete_token(project_id):
    """
    .. todo::
        Implement, document
    """
    _payload = fingerprint({
        'method': 'DELETE',
        'url': '/' + project_id
    })
