import json
from datetime import datetime, timedelta

from aiohttp import web
import jwt
from aiohttp_swagger import *

from app.models import get_model_by_name
from app.services.serializers import serialize_body

@swagger_path('swagger/login.yaml')
@serialize_body('login_schema', custom_exc=web.HTTPUnauthorized)
async def login(request: web.Request, body) -> web.Response:
    user_table = get_model_by_name('user')

    user = await request.app['pg'].fetchrow(user_table.select().where(user_table.c.login == body['login']))

    if not user:
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Invalid username / password combination'}),
                                   content_type='application/json')

    if body['password'] == user['password']:
        response = web.json_response(data={'user_id': user['id']}, status=200)
        max_age = timedelta(hours=24)
        expiration_time = datetime.utcnow() + max_age
        token = jwt.encode(payload={'login': user['login'],
                                    'user_id': user['id'],
                                    'exp': expiration_time},
                           key='secret')
        response.set_cookie(name='AppCoockie',
                            value=token.decode(),
                            httponly=True,
                            secure=False,
                            path='/',
                            max_age=int(max_age.total_seconds()),
                            # expires=expiration_time.isoformat(), 
        )
        return response

    raise web.HTTPUnauthorized(
        body=json.dumps({'error': 'Invalid username / password combination'}), content_type='application/json')

@swagger_path('swagger/logout.yaml')
async def logout(request: web.Request) -> web.Response:
    response = web.json_response({'status': 'Ok'})
    response.del_cookie(name='AppCoockie')
    return response
