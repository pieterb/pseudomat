from pseudomat.common import fingerprint


def test_project(db):
    sub = "TestProject1"
    jti = fingerprint(sub)
    db.delete_project(jti)
    assert db.delete_project(jti) is False

    assert db.create_project(
        jti=jti,
        sub=sub,
        iss='pieter@djinnit.com',
        psig='psig',
        penc='penc',
        ssig='ssig',
        senc='senc',
        jws='foobar'
    ) is True

    assert db.create_project(
        jti=jti,
        sub=sub,
        iss='pieter2@djinnit.com',
        psig='psig',
        penc='penc',
        ssig='ssig',
        senc='senc',
        jws='foobar'
    ) is False

    assert db.get_project(jti) == {
        'jti': 'XTBthkz4Ku6Ug0OpvOTwmeKxXpQ3dpui',
        'sub': 'TestProject1',
        'iss': 'pieter@djinnit.com',
        'psig': 'psig',
        'penc': 'penc',
        'ssig': 'ssig',
        'senc': 'senc',
        'jws': 'foobar',
    }

    assert db.delete_project(jti) is True


def test_config(db):
    db.set_config('foo', None)
    assert db.get_config('foo') is None
    db.set_config('foo', 'bar')
    assert db.get_config('foo') == 'bar'
    db.set_config('foo', 'baz')
    assert db.get_config('foo') == 'baz'
    db.set_config('foo', None)
    assert db.get_config('foo') is None
