# language=rst
"""

This module uses aiopg for asynchronous query execution, and the SQLAlchemy core
query builder.

"""

from functools import lru_cache
import logging
import typing as T

from aiohttp import web
import aiopg.sa
import psycopg2
import sqlalchemy.sql.functions as sa_functions
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa

from pseudomat.common import fingerprint

_logger = logging.getLogger(__name__)


class PreconditionFailed(Exception):
    pass


@lru_cache()
def metadata() -> sa.MetaData:
    retval = sa.MetaData()

    sa.Table(
        'project', retval,
        sa.Column('jti', postgresql.CHAR(length=32)),
        sa.Column('iss', postgresql.VARCHAR(length=80)),
        sa.Column('sub', postgresql.VARCHAR(length=80)),
        sa.Column('iat', postgresql.INTEGER),
        sa.Column('psig', postgresql.TEXT()),
        sa.Column('penc', postgresql.TEXT()),
        sa.Column('jws', postgresql.TEXT()),
        sa.Column('last_modified', postgresql.TIMESTAMP(timezone=None),
                  server_default=sa_functions.now())
    )

    sa.Table(
        'invite', retval,
        sa.Column('sub', postgresql.VARCHAR(length=80)),
        sa.Column('jws', postgresql.TEXT(), nullable=False),
        sa.Column('iat', postgresql.INTEGER),
        sa.Column('iss', postgresql.CHAR(length=32), sa.ForeignKey('project.jti')),
        sa.Column('jti', postgresql.CHAR(length=32), primary_key=True),
        sa.Column('psig', postgresql.TEXT()),
        sa.Column('penc', postgresql.TEXT()),
        sa.Column('last_modified', postgresql.TIMESTAMP(timezone=None),
                  server_default=sa_functions.now())
    )

    # sa.Table(
    #     'AccountRoles', retval,
    #     sa.Column('account_id', sa.String, index=True, nullable=False, primary_key=True),
    #     sa.Column('role_ids', postgresql.ARRAY(sa.String(32)), nullable=False),
    #     sa.Column('log_id', sa.Integer, sa.ForeignKey('AccountRolesLog.id'),
    #               index=True, nullable=False, unique=True),
    #     sa.Index('idx_ar_role_ids', 'role_ids', postgresql_using='gin')
    # )

    return retval


def context(app):
    dbconf = app['config']['postgres']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['dbname'])
    return aiopg.sa.create_engine(
        user=dbconf['user'],
        database=dbconf['dbname'],
        host=dbconf['host'],
        port=dbconf['port'],
        password=dbconf['password'],
        client_encoding='utf8'
    )


async def initialize_schema(app):
    async with app['engine'].acquire() as conn:
        pass


async def create_project(
    app: web.Application,
    jti: str,
    iss: str,
    sub: str,
    iat: int,
    psig: str,
    penc: str,
    jws: str
) -> bool:
    """

    Raises:
        PreconditionFailed: if another project with this email/name exists.

        SeeOther: if the project already exists.

    """
    project = metadata().tables['project']
    async with app['engine'].acquire() as conn:
        try:
            await conn.execute(
                project.insert().values(
                    jti=jti,
                    iss=iss,
                    sub=sub,
                    iat=iat,
                    psig=psig,
                    penc=penc,
                    jws=jws
                )
            )
        except psycopg2.IntegrityError:
            result_proxy = await conn.execute(
                sa.select([sa.func.count()]).select_from(project)
                .where(project.c.jws == jws)
            )
            result = await result_proxy.fetchone()
            if result[0] == 1:
                return False
            else:
                raise web.HTTPForbidden(
                    text="Another project with the same e-mail address and name exists."
                )
    return True


async def delete_project(app, project_id: str):
    project = metadata().tables['project']
    async with app['engine'].acquire() as conn:
        await conn.execute(
            project.delete().where(project.c.jti == project_id)
        )


async def get_project(app, project_id: str) -> T.Optional[dict]:
    project = metadata().tables['project']
    async with app['engine'].acquire() as conn:
        result_proxy = await conn.execute(
            sa.select([project]).select_from(project)
            .where(project.c.jti == project_id)
        )
        result = await result_proxy.fetchone()
        if result is None:
            return None
        return dict(result.items())


async def create_invite(
    app: web.Application,
    jti: str,
    iss: str,
    sub: str,
    iat: int,
    psig: str,
    penc: str,
    jws: str
) -> bool:
    """

    Raises:
        PreconditionFailed: if another project with this email/name exists.

        SeeOther: if the project already exists.

    """
    invite = metadata().tables['invite']
    async with app['engine'].acquire() as conn:
        try:
            await conn.execute(
                invite.insert().values(
                    jti=jti,
                    iss=iss,
                    sub=sub,
                    iat=iat,
                    psig=psig,
                    penc=penc,
                    jws=jws
                )
            )
        except psycopg2.IntegrityError:
            result_proxy = await conn.execute(
                sa.select([sa.func.count()]).select_from(invite)
                .where(invite.c.jws == jws)
            )
            result = await result_proxy.fetchone()
            if result[0] == 1:
                return False
            else:
                raise web.HTTPForbidden(
                    text="Another invite with the same name exists."
                )
    return True


# async def _accountroleslog_insert(
#     conn,
#     created_by: str,
#     request_info: str,
#     account_id: str,
#     action: str,
#     role_ids: T.Iterable[str]
# ) -> int:
#     # language=rst
#     """
#
#     Insert an entry in the audit log, and return the *log id*.
#
#     """
#     accountroleslog_table = metadata().tables['AccountRolesLog']
#     result_set = await conn.execute(
#         accountroleslog_table.insert().values(
#             created_by='authz_admin_service',
#             request_info='Initialization',
#             account_id=account_id,
#             action='C',
#             role_ids=role_ids
#         ).returning(accountroleslog_table.c.id)
#     )
#     row = await result_set.fetchone()
#     return row[0]


# async def accounts(request, role_ids=None):
#     accountroles = metadata().tables['AccountRoles']
#     statement = sa.select([accountroles])
#     if role_ids is not None:
#         statement = statement.where(accountroles.c.role_ids.contains(
#             sa.cast(role_ids, postgresql.ARRAY(sa.String(32)))
#         ))
#     async with request.app['engine'].acquire() as conn:
#         async for row in conn.execute(
#             statement
#         ):
#             yield row


# async def account_names_with_role(request, role_id):
#     accountroles_table = metadata().tables['AccountRoles']
#     async with request.app['engine'].acquire() as conn:
#         async for row in conn.execute(
#             sa.select([accountroles_table.c.account_id])
#                 .where(accountroles_table.c.role_ids.contains(
#                 sa.cast([role_id], postgresql.ARRAY(sa.String(32))))
#             )
#         ):
#             yield row['account_id']


# async def account(request, account_id):
#     accountroles_table = metadata().tables['AccountRoles']
#     async with request.app['engine'].acquire() as conn:
#         result_proxy = await conn.execute(
#             sa.select([accountroles_table])
#             .where(accountroles_table.c.account_id == account_id)
#         )
#         return await result_proxy.fetchone()


# async def delete_account(request, account):
#     # language=rst
#     """
#
#     Raises:
#         PreconditionFailed: if the account doesn't exist or isn't in the
#             expected state.
#
#     """
#     account_data = await account.data()
#     accountroles = metadata().tables['AccountRoles']
#     async with request.app['engine'].acquire() as conn:
#         async with conn.begin():
#             log_id = await _accountroleslog_insert(
#                 conn,
#                 created_by='p.van.beek@amsterdam.nl',
#                 request_info=str(request.headers),
#                 account_id=account['account'],
#                 action='D',
#                 role_ids=account_data['role_ids']
#             )
#             result_set = await conn.execute(
#                 accountroles.delete().where(sa.and_(
#                     accountroles.c.account_id == account['account'],
#                     accountroles.c.log_id == account_data['log_id']
#                 ))
#             )
#             if result_set.rowcount != 1:
#                 raise PreconditionFailed()
#     return log_id


# async def update_account(request, account, role_ids):
#     # language=rst
#     """
#
#     Raises:
#         PreconditionFailed: if the account doesn't exist or isn't in the
#             expected state.
#
#     """
#     account_data = await account.data()
#     accountroles = metadata().tables['AccountRoles']
#     async with request.app['engine'].acquire() as conn:
#         async with conn.begin():
#             log_id = await _accountroleslog_insert(
#                 conn,
#                 created_by='p.van.beek@amsterdam.nl',
#                 request_info=str(request.headers),
#                 account_id=account['account'],
#                 action='U',
#                 role_ids=role_ids
#             )
#             result_set = await conn.execute(
#                 accountroles.update().where(sa.and_(
#                     accountroles.c.account_id == account['account'],
#                     accountroles.c.log_id == account_data['log_id']
#                 )).values(
#                     role_ids=role_ids,
#                     log_id=log_id
#                 )
#             )
#             if result_set.rowcount != 1:
#                 raise PreconditionFailed()
#     return log_id


# async def initialize_database(
#     engine,
#     required_accounts: T.Dict[str, T.Iterable[str]]
# ):
#     # language=rst
#     """
#
#     Raises:
#         PreconditionFailed: if a race condition exists between this process and
#             another process trying to initialize the database at the same time.
#
#     """
#     accountroles_table = metadata().tables['AccountRoles']
#     async with engine.acquire() as conn:
#         for account_id, role_ids in required_accounts.items():
#             result_proxy = await conn.execute(
#                 sa.select([sa_functions.count('*')])
#                     .select_from(accountroles_table)
#                     .where(accountroles_table.c.account_id == account_id)
#             )
#             row = await result_proxy.fetchone()
#             if row[0] == 0:
#                 _logger.info("Required account '%s' not found. Creating this account with roles %s", account_id, repr(role_ids))
#                 async with conn.begin():
#                     log_id = await _accountroleslog_insert(
#                         conn,
#                         created_by='authz_admin_service',
#                         request_info='Initialization',
#                         account_id=account_id,
#                         action='C',
#                         role_ids=role_ids
#                     )
#                     try:
#                         await conn.execute(
#                             accountroles_table.insert().values(
#                                 account_id=account_id,
#                                 role_ids=role_ids,
#                                 log_id=log_id
#                             )
#                         )
#                     except sa_exceptions.IntegrityError:
#                         raise PreconditionFailed() from None
