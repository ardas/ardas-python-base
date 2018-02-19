import sqlalchemy as sa

from aiohttp_security.abc import AbstractAuthorizationPolicy
# from passlib.hash import sha256_crypt
from app.models import User, Permission


class DBAuthorizationPolicy(AbstractAuthorizationPolicy):
    def __init__(self, pg):
        self.pg = pg

    async def authorized_userid(self, identity):
        async with self.pg as conn:
            where = sa.and_(User.c.login == identity,
                            sa.not_(User.c.disabled))
            query = User.count().where(where)
            ret = await conn.scalar(query)
            if ret:
                return identity
            else:
                return None

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False

        async with self.pg as conn:
            where = (User.c.login == identity)
            query = User.select().where(where)
            ret = await conn.execute(query)
            user = await ret.fetchone()
            if user is not None:
                user_id = user[0]
                is_superuser = user[3]
                if is_superuser:
                    return True

                where = Permission.c.user_id == user_id
                query = Permission.select().where(where)
                ret = await conn.execute(query)
                result = await ret.fetchall()
                if ret is not None:
                    for record in result:
                        if record.perm_name == permission:
                            return True

            return False


# async def check_credentials(db_engine, username, password):
#     async with db_engine as conn:
#         where = (User.c.login == username)
#         query = User.select().where(where)
#         ret = await conn.execute(query)
#         user = await ret.fetchone()
#         if user is not None:
#             hash = user[2]
#             return sha256_crypt.verify(password, hash)
#     return False

PUBLIC_RESOURCES = (
    ('/api/v1/auth/login', ('POST',)),
    ('/api/v1/user', ('POST',)),
    ('/api/version', ('GET',)),
    ('/api/v1/doc', ('GET',)),
    ('/_debugtoolbar', ('GET',)),
)


def check_public_resources(path: str, method: str) -> bool:
    for resource, allowed_methods in PUBLIC_RESOURCES:
        if resource in path and method in allowed_methods:
            return True
    return False
