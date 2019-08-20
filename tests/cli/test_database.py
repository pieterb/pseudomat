import time

import pytest
from sqlalchemy.orm.exc import FlushError

from pseudomat.cli import database as db
from pseudomat import common


def test_project():
    project = db.get_project(sub="TestProject1")
    if project is not None:
        db.delete_project(project)

    project1 = db.Project(
        jti=common.fingerprint("TestProject1"),
        sub="TestProject1",
        iat=int(time.time()),
        iss='pieter@djinnit.com',
        psig='psig',
        penc='penc',
        ssig='ssig',
        senc='senc',
        jws='foobar'
    )
    db.add_project(project1)

    project2 = db.Project(
        jti=common.fingerprint("TestProject1"),
        sub="TestProject1",
        iat=int(time.time()),
        iss='pieter2@djinnit.com',
        psig='psig',
        penc='penc',
        ssig='ssig',
        senc='senc',
        jws='foobar'
    )

    with pytest.raises(FlushError):
        db.add_project(project2)

    db.delete_project(project1)


def test_config():
    db.set_config('foo', None)
    assert db.get_config('foo') is None
    db.set_config('foo', 'bar')
    assert db.get_config('foo') == 'bar'
    db.set_config('foo', 'baz')
    assert db.get_config('foo') == 'baz'

