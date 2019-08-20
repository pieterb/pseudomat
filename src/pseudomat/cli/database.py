from functools import lru_cache, wraps
import logging
import typing as T

from sqlalchemy.dialects import sqlite
import sqlalchemy.exc
import sqlalchemy.orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

from .. import common
from . import globals

_logger = logging.getLogger(__name__)
IntegrityError = sa.exc.IntegrityError
Base = declarative_base()


def autocommit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            retval = f(*args, **kwargs)
            session().commit()
            return retval
        except Exception:
            session().rollback()
            raise
    return wrapper


@lru_cache()
def session() -> sa.orm.Session:
    engine = sa.create_engine(
        'sqlite:///' + str(globals.config_dir() / 'cli.db'),
        isolation_level='SERIALIZABLE'
    )
    connection = engine.connect()
    connection.execute('pragma foreign_keys=ON')
    retval: sa.orm.Session = sa.orm.sessionmaker(bind=connection)()
    return retval


class Config(Base):
    __tablename__ = 'config'

    key = sa.Column(sqlite.VARCHAR(80), primary_key=True)
    value = sa.Column(sqlite.TEXT)


def get_config(key: str):
    config = session().query(Config).filter_by(key=key).first()
    return None if config is None else config.value


@autocommit
def set_config(key: str, value: T.Optional[str] = None):
    """
    Parameters:
        key: name of the config value to set.
        value: The new value, or `None`.
    """
    s = session()
    config = s.query(Config).filter_by(key=key).first()
    if value is None:
        if config is not None:
            s.delete(config)
    elif config is None:
        config = Config(key=key, value=value)
        s.add(config)
    else:
        config.value = value


class Project(Base):

    __tablename__ = 'project'

    jti = sa.Column('jti', sqlite.CHAR(length=32), nullable=False, primary_key=True)
    sub = sa.Column('sub', sqlite.VARCHAR(length=80), nullable=False, unique=True)
    iss = sa.Column('iss', sqlite.VARCHAR(length=255), nullable=False)
    iat = sa.Column('iat', sqlite.INTEGER(), nullable=False)
    psig = sa.Column('psig', sqlite.TEXT(), nullable=False, unique=True)
    penc = sa.Column('penc', sqlite.TEXT(), nullable=False, unique=True)
    ssig = sa.Column('ssig', sqlite.TEXT())
    senc = sa.Column('senc', sqlite.TEXT())
    jws = sa.Column('jws', sqlite.TEXT(), nullable=False)


def get_projects():
    return session().query(Project).all()


def get_project(jti=None, sub=None):
    if jti is None:
        jti = common.fingerprint(sub)
    return session().query(Project).filter_by(jti=jti).first()


@autocommit
def add_project(project: Project):
    session().add(project)


@autocommit
def delete_project(project: Project):
    session().delete(project)


class Invite(Base):

    __tablename__ = 'invite'

    jti = sa.Column('jti', sqlite.CHAR(length=32), nullable=False, primary_key=True)
    sub = sa.Column('sub', sqlite.VARCHAR(length=80), nullable=False, unique=True)
    iss = sa.Column('iss', sqlite.CHAR(length=32), sa.ForeignKey('project.jti'), nullable=False)
    iat = sa.Column('iat', sqlite.INTEGER(), nullable=False)
    psig = sa.Column('psig', sqlite.TEXT(), nullable=False, unique=True)
    penc = sa.Column('penc', sqlite.TEXT(), nullable=False, unique=True)
    ssig = sa.Column('ssig', sqlite.TEXT())
    senc = sa.Column('senc', sqlite.TEXT())
    pjws = sa.Column('pjws', sqlite.TEXT(), nullable=False)
    sjws = sa.Column('sjws', sqlite.TEXT(), nullable=False)


def get_invites(project_id):
    return session().query(Invite).filter_by(iss=project_id).all()


def get_invite(jti=None, iss=None, sub=None):
    if jti is None:
        jti = common.fingerprint([iss, sub])
    return session().query(Invite).filter_by(jti=jti).first()


@autocommit
def add_invite(invite: Invite):
    session().add(invite)


@autocommit
def delete_invite(invite: Invite):
    session().delete(invite)
