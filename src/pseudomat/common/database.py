from functools import lru_cache
import logging
import typing as T

from sqlalchemy.dialects import sqlite
import sqlalchemy.event
from sqlalchemy.exc import DBAPIError, IntegrityError
import sqlalchemy as sa

_logger = logging.getLogger(__name__)
_engine: T.Optional[sa.engine.Engine] = None

_DDL = """
create table config
(
    key varchar not null
        constraint config_pk
            primary key,
    value text
);;

create table member_jws
(
    jti char(32) not null
        constraint member_jws_pk
            primary key,
    jws text not null,
    prev_jti char(32) not null
);;

create unique index member_jws_prev_jti_uindex
    on member_jws (prev_jti);;

create table project
(
    jti char(32) not null
        constraint project_pk
            primary key,
    sub varchar(80) collate NOCASE not null,
    iss varchar(255) collate NOCASE not null,
    psig text not null,
    penc text not null,
    ssig text,
    senc text,
    jws text not null
);;

create table member
(
    project_jti char(32) not null
        references project
            on update cascade on delete cascade,
    invite_jti char(32) not null
        constraint member_pk
            primary key
        references member_jws
            on update cascade on delete set null,
    invite_sub varchar(80) collate NOCASE not null,
    invite_sig text not null,
    invite_enc text not null,
    member_jti char(32)
        references member_jws
            on update cascade on delete set null,
    member_sig text,
    member_enc text,
    revoke_jti char(32)
        references member_jws
            on update cascade on delete set null
);;

create unique index member_name_uindex
    on member (project_jti, invite_sub);;

CREATE TRIGGER after_member_delete after delete on member
begin
    delete from member_jws where jti = old.invite_jti;
    delete from member_jws where jti = old.member_jti;
    delete from member_jws where jti = old.revoke_jti;
end;;

insert into config (key, value) VALUES ('schema', '1')
"""


def initialize_database(filepath):
    teardown_database()
    _logger.debug("Connecting to sqlite database: %s", filepath)
    global _engine
    _engine = sa.create_engine(
        'sqlite:///%s' % filepath,
        # This is the default, but the sqlalchemy documentation recommends specifying it anyway:
        isolation_level='SERIALIZABLE'
    )
    try:
        _schema = get_config('schema')
        assert _schema == '1'
    except DBAPIError:
        with _engine.connect() as connection:
            for stmt in _DDL.split(';;'):
                connection.execute(stmt)


def teardown_database(_exc=None):
    if _engine is not None:
        _engine.dispose()


@sa.event.listens_for(sa.engine.Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record):
    _logger.debug("Executing PRAGMA foreign_keys=ON")
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@lru_cache()
def metadata() -> sa.MetaData:
    retval = sa.MetaData()

    sa.Table(
        'config', retval,
        sa.Column('key', sqlite.VARCHAR(80), primary_key=True),
        sa.Column('value', sqlite.TEXT, nullable=False)
    )

    sa.Table(
        'member', retval,
        sa.Column('project_jti', sqlite.CHAR(length=32), sa.ForeignKey('project.jti'), nullable=False),
        sa.Column('invite_jti', sqlite.CHAR(length=32), sa.ForeignKey('member_jws.jti'), nullable=False, primary_key=True),
        sa.Column('invite_sub', sqlite.VARCHAR(length=80, collation='NOCASE'), nullable=True),
        sa.Column('invite_sig', sqlite.TEXT(), nullable=False),
        sa.Column('invite_enc', sqlite.TEXT(), nullable=False),
        sa.Column('member_jti', sqlite.CHAR(length=32), sa.ForeignKey('member_jws.jti')),
        sa.Column('member_sig', sqlite.TEXT(), nullable=False),
        sa.Column('member_enc', sqlite.TEXT(), nullable=False),
        sa.Column('revoke_jti', sqlite.CHAR(length=32), sa.ForeignKey('member_jws.jti')),
        sa.UniqueConstraint('project_jti', 'invite_sub')
    )

    sa.Table(
        'member_jws', retval,
        sa.Column('jti', sqlite.CHAR(length=32), primary_key=True),
        sa.Column('jws', sqlite.TEXT(), nullable=False),
        sa.Column('prev_jti', sqlite.CHAR(length=32), nullable=False, unique=True)
    )

    sa.Table(
        'project', retval,
        sa.Column('jti', sqlite.CHAR(length=32), nullable=False, primary_key=True),
        sa.Column('sub', sqlite.VARCHAR(length=80, collation='NOCASE'), nullable=False),
        sa.Column('iss', sqlite.VARCHAR(length=255, collation='NOCASE'), nullable=False),
        sa.Column('psig', sqlite.TEXT(), nullable=False, unique=True),
        sa.Column('penc', sqlite.TEXT(), nullable=False, unique=True),
        sa.Column('ssig', sqlite.TEXT()),
        sa.Column('senc', sqlite.TEXT()),
        sa.Column('jws', sqlite.TEXT(), nullable=False)
    )

    return retval


def create_project(
    jti: str,
    iss: str,
    sub: str,
    psig: str,
    penc: str,
    jws: str,
    ssig: T.Optional[str] = None,
    senc: T.Optional[str] = None
) -> bool:
    project = metadata().tables['project']
    with _engine.connect() as conn:
        try:
            conn.execute(
                project.insert().values(
                    jti=jti,
                    iss=iss,
                    sub=sub,
                    psig=psig,
                    penc=penc,
                    ssig=ssig,
                    senc=senc,
                    jws=jws
                )
            )
        except IntegrityError:
            p = get_project(jti)
            return p['jws'] == jws
    return True


def get_project(project_id: str) -> T.Optional[dict]:
    project = metadata().tables['project']
    result_proxy = _engine.execute(
        sa.select([project]).select_from(project)
        .where(project.c.jti == project_id)
    )
    result = result_proxy.first()
    return None if result is None else dict(result.items())


def get_projects() -> T.List[dict]:
    project = metadata().tables['project']
    result_proxy = _engine.execute(
        sa.select([project]).select_from(project)
    )
    retval = []
    for row in result_proxy:
        retval.append(dict(row))
    return retval


def delete_project(project_id: str) -> bool:
    project = metadata().tables['project']
    result: sa.engine.ResultProxy = _engine.execute(project.delete().where(project.c.jti == project_id))
    return result.rowcount > 0


def set_config(key: str, value: T.Optional[str]):
    config = metadata().tables['config']
    with _engine.begin() as c:
        c.execute(config.delete().where(config.c.key == key))
        if value is not None:
            c.execute(config.insert().values(key=key, value=value))


def get_config(key: str) -> T.Optional[str]:
    config = metadata().tables['config']
    result = _engine.execute(sa.select([config.c.value]).where(config.c.key == key))
    row = result.first()
    return None if row is None else row[0]
