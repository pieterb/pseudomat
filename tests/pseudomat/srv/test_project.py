# language=rst
"""
.. todo:: Check values that are being returned on GET project.
"""


PROJECT_JWS='eyJhbGciOiJFZERTQSIsInR5cCI6InByb2plY3QifQ.eyJpYXQiOjE1Njc3OTIyODIsImlzcyI6InBpZXRlckBkamlubml0LmNvbSIsImp0aSI6IlVlT096SkwxS3ZZX1l0b1prRzBsWWFiWEVSRFhQbF8xIiwicGVuYyI6eyJjcnYiOiJYNDQ4Iiwia3R5IjoiT0tQIiwidXNlIjoiZW5jIiwieCI6InhDX0pkY1dFeFdhMl9vZWZwT0E1R0lyczFPelgyM1dxX3ZFNUtOWno3ejVlaFA3ZjJZN2ZkVktjNFNyYzBpZjV2d0VJMXpjMWFYZyJ9LCJwc2lnIjp7ImNydiI6IkVkNDQ4Iiwia3R5IjoiT0tQIiwidXNlIjoic2lnIiwieCI6InB6bW5kVmJfeEdWckRqaDJXenN1QkhHU1ZjbkpTcTVoMTVURnYza2I3clB1VGEwOEkydFY2dVlRY096Zl8wNDd4cV9VM0IwRVhERUEifSwic3ViIjoiTXkgUHJvamVjdCJ9.Rn78c_WrgYOaGUG4N8PjOVV6q67fkc0QLYUxWsFx7wr5htMGKQjCQt-Qm8FVqbSXYQ0snnrJYKwAyOt_au_AbAGMDMKYWrN18B3AZFWd-rKTLJS6ckyV_fsaAWlzpMF5XJCzKg2DfVd_dE013VxDQykA'
PROJECT_JWS_BAD_SIG='eyJhbGciOiJFZERTQSIsInR5cCI6InByb2plY3QifQ.eyJpYXQiOjE1Njc3OTIyODIsImlzcyI6InBpZXRlckBkamlubml0LmNvbSIsImp0aSI6IlVlT096SkwxS3ZZX1l0b1prRzBsWWFiWEVSRFhQbF8xIiwicGVuYyI6eyJjcnYiOiJYNDQ4Iiwia3R5IjoiT0tQIiwidXNlIjoiZW5jIiwieCI6InhDX0pkY1dFeFdhMl9vZWZwT0E1R0lyczFPelgyM1dxX3ZFNUtOWno3ejVlaFA3ZjJZN2ZkVktjNFNyYzBpZjV2d0VJMXpjMWFYZyJ9LCJwc2lnIjp7ImNydiI6IkVkNDQ4Iiwia3R5IjoiT0tQIiwidXNlIjoic2lnIiwieCI6InB6bW5kVmJfeEdWckRqaDJXenN1QkhHU1ZjbkpTcTVoMTVURnYza2I3clB1VGEwOEkydFY2dVlRY096Zl8wNDd4cV9VM0IwRVhERUEifSwic3ViIjoiTXkgUHJvamVjdCJ9.Rn78c_WrgYOaGUG4N8PjOVV6q67fkc0QLYUxWsFx7wr5htMGKQjCQt-Qm8FVqbSXYQ0snnrJYKwAyOt_au_AbAGMDMKYWrN18B3AZFWd-rKTLJS6ckyV_fsaAWlzpMF5XJCzKg2DfVd_dE013VxDQylA'


def test_get_root(client):
    rv = client.get('/')
    assert rv.status_code == 405  # Method Not Allowed
    assert rv.allow == {'OPTIONS', 'POST'}
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root_no_length(client):
    rv = client.post(
        path="/",
        content_type='text/plain'
    )
    assert rv.status_code == 411
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root_too_large(client):
    rv = client.post(
        path="/",
        data='0123456789abcdef' * 64 * 128,  # 128k (max is 64k)
        content_type='application/jose'
    )
    assert rv.status_code == 413
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root_non_ascii(client):
    rv = client.post(
        path="/",
        data='¡Holá!',
        content_type='application/jose'
    )
    assert rv.status_code == 400
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root_unsupported_media_type(client):
    rv = client.post(
        path="/",
        data=PROJECT_JWS,
        content_type='text/plain'
    )
    assert rv.status_code == 415
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root_bad_sig(client):
    rv = client.post(
        path="/",
        data=PROJECT_JWS_BAD_SIG,
        content_type='application/jose'
    )
    assert rv.status_code == 422
    assert rv.content_type == 'text/plain; charset=utf-8'


def test_post_root(client):
    rv = client.post(
        path="/",
        data=PROJECT_JWS,
        content_type='application/jose'
    )
    assert rv.status_code == 201
    assert rv.content_type == 'text/plain; charset=utf-8'
    assert rv.headers['Location'] == 'http://localhost/UeOOzJL1KvY_YtoZkG0lYabXERDXPl_1'
