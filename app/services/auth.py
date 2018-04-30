import json
import secrets

import sqlalchemy as sa
from datetime import datetime, timedelta

from aiohttp_security.abc import AbstractAuthorizationPolicy
from aiohttp import web
import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidAudienceError, MissingRequiredClaimError
from aioredis import Redis
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
    ('/api/v1/restorepassword', ('POST',)),
    ('/api/v1/user/password/new', ('POST',)),
    ('/api/v1/restorepassword/', ('GET',)),
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


async def set_authorization_cookie(user: dict, timedelta_data: dict, secret_key: str, audience=None):
    response = web.json_response(data={'status': 'ok'}, status=200)
    max_age = timedelta(**timedelta_data)
    expiration_time = datetime.utcnow() + max_age
    payload = {'login': user['login'],
               'user_id': user['user_id'],
               'exp': expiration_time}

    if audience:
        payload.update({'aud': audience})

    token = jwt.encode(payload=payload,
                       key=secret_key)
    response.set_cookie(name='AppCookie',
                        value=token.decode(),
                        httponly=True,
                        secure=False,
                        path='/',
                        max_age=int(max_age.total_seconds()),
                        # expires=expiration_time.isoformat(), 
    )
    return response


async def set_authorization_cookie_redis(user: dict, timedelta_data: dict, redis: Redis):
    response = web.json_response(data={'status': 'ok'}, status=200)
    max_age = int(timedelta(**timedelta_data).total_seconds())
    payload = {'login': user['login'],
               'user_id': user['user_id']}
    token = secrets.token_hex()
    await redis.setex(token, max_age, json.dumps(payload))
    response.set_cookie(name='AppCookie',
                        value=token,
                        httponly=True,
                        secure=False,
                        path='/',
                        max_age=max_age,
                        )
    return response


def token_decode(token, secret_key, audience=None):
    try:
        data = jwt.decode(token, key=secret_key, audience=audience)
    except ExpiredSignatureError:
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Token expired'}),
                                   content_type='application/json')
    except (InvalidAudienceError, DecodeError, MissingRequiredClaimError):
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Invalid token'}),
                                   content_type='application/json')
    return data
