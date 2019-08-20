from jwcrypto import jwk, jws, jwt


def create_authz_token(iss: str, url: str, method: str, key: jwk.JWK) -> str:
    token = jwt.JWT(
        header={
            'alg': 'EdDSA'
        },
        claims={
            'url': url,
            'method': method.upper()
        },
        default_claims={
            'iat': None,
            'iss': iss
        }
    )
    token.make_signed_token(key)
    return token.serialize()
