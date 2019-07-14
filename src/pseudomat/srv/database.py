# language=rst
"""

.. todo:: Automatic schema creation and schema updates on target platforms.

    Currently, creating or upgrading the database schema on acceptance and
    production is automated in the deploy lane.

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
import sqlalchemy.exc as sa_exceptions
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


_logger = logging.getLogger(__name__)


class PreconditionFailed(Exception):
    pass


@lru_cache()
def metadata() -> sa.MetaData:
    retval = sa.MetaData()

    sa.Table(
        'project', retval,
        sa.Column('id', postgresql.CHAR(length=43), index=True, nullable=False, primary_key=True),
        sa.Column('jws', postgresql.TEXT(), index=True, nullable=False, unique=True),
        sa.Column('verified', postgresql.BOOLEAN(), index=True, nullable=False, server_default='FALSE'),
        sa.Column('sig_key', postgresql.TEXT(), nullable=False),
        sa.Column('enc_key', postgresql.TEXT(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=None), index=True, nullable=False, server_default=sa_functions.now())
    )

    sa.Table(
        'invite', retval,
        sa.Column('id', postgresql.INTEGER(), autoincrement=True, index=True, nullable=False, primary_key=True),
        sa.Column('jws', postgresql.TEXT(), nullable=False),
        sa.Column('project_id', postgresql.CHAR(length=43), sa.ForeignKey('project.id'), nullable=False),
        sa.Column('name', postgresql.VARCHAR(length=80), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=None), server_default=sa_functions.now(), index=True, nullable=False),
        sa.UniqueConstraint('project_id', 'name', name='invite_pk_2')
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


async def initialize_app(app):
    dbconf = app['config']['postgres']
    _logger.info("Connecting to database: postgres://%s:%i/%s",
                 dbconf['host'], dbconf['port'], dbconf['dbname'])
    engine_context = aiopg.sa.create_engine(
        user=dbconf['user'],
        database=dbconf['dbname'],
        host=dbconf['host'],
        port=dbconf['port'],
        password=dbconf['password'],
        client_encoding='utf8'
    )
    app['engine'] = await engine_context.__aenter__()
    #await check_introspection(app['engine'])
    #await initialize_database(app['engine'], required_accounts=app['config']['authz_admin']['required_accounts'])

    async def on_shutdown(app):
        await engine_context.__aexit__(None, None, None)
    app.on_shutdown.append(on_shutdown)


#async def check_introspection(engine):


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


async def create_project(request: web.Request, project_id: str, jws: str, sig_key: str, enc_key: str):
    """

    Raises:
        PreconditionFailed: if another project with this email/name exists.

        SeeOther: if the project already exists.

    """
    project = metadata().tables['project']
    async with request.app['engine'].acquire() as conn:
        try:
            await conn.execute(
                project.insert().values(
                    id=project_id,
                    jws=jws,
                    sig_key=sig_key,
                    enc_key=enc_key
                )
            )
        except psycopg2.IntegrityError:
            result_proxy = await conn.execute(
                sa.select([sa.func.count()]).select_from(project)
                .where(project.c.jws == jws)
            )
            result = await result_proxy.fetchone()
            if result[0] == 1:
                raise web.HTTPSeeOther(
                    location=str(request.rel_url / project_id)
                )
            else:
                raise web.HTTPPreconditionFailed(
                    reason="Another project with the same e-mail address and name exists."
                )


async def create_invite(request: web.Request, project_id: str, jws: str, name: str):
    """

    Raises:
        PreconditionFailed: if another invite with this project_id/name exists.

    """
    invite = metadata().tables['invite']
    async with request.app['engine'].acquire() as conn:
        try:
            await conn.execute(
                invite.insert().returning(invite.c.id).values(
                    project_id=project_id,
                    jws=jws,
                    name=name
                )
            )
        except psycopg2.IntegrityError:
            project = metadata().tables['project']
            result_proxy = await conn.execute(
                sa.select([sa.func.count()]).select_from(project)
                .where(project.c.id == project_id)
            )
            result = await result_proxy.fetchone()
            if result[0] == 0:
                raise web.HTTPNotFound()
            raise web.HTTPPreconditionFailed(
                reason="That invite was already issued."
            )


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
