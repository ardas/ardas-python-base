import json
from datetime import datetime, timedelta

from aiohttp import web
import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidAudienceError
from aiohttp_swagger import *
from sqlalchemy import and_, select, exists, literal_column

from app.models import get_model_by_name, row_to_dict
from app.services.serializers import serialize_body
from app.services.email import Email
from app.services.auth import set_authorization_coockie, token_decode


auth_routes = web.RouteTableDef()


@swagger_path('swagger/login.yaml')
@auth_routes.post('/api/v1/auth/login')
@serialize_body('login_schema', custom_exc=web.HTTPUnauthorized)
async def login(request: web.Request, body) -> web.Response:
    user_table = get_model_by_name('user')

    user = await request.app['pg'].fetchrow(user_table.select().where(user_table.c.login == body['login']))

    if not user:
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Invalid username / password combination'}),
                                   content_type='application/json')

    if body['password'] == user['password']:
        return await set_authorization_coockie(user, {'hours': 24}, request.app['config']['SECRET_KEY'])

    raise web.HTTPUnauthorized(
        body=json.dumps({'error': 'Invalid username / password combination'}), content_type='application/json')


@swagger_path('swagger/logout.yaml')
@auth_routes.get('/api/v1/auth/logout')
async def logout(request: web.Request) -> web.Response:
    response = web.json_response({'status': 'ok'})
    response.del_cookie(name='AppCoockie')
    return response


@swagger_path('swagger/restore_password_post.yaml')
@auth_routes.post('/api/v1/restorepassword')
@serialize_body('forgot_password')
async def forgot_password(request: web.Request, body) -> web.Response:
    # check is user exist
    user_table = get_model_by_name('user')
    user = await request.app['pg'].fetchrow(user_table.select().where(
        user_table.c.login == body['login']))
    
    if not user: 
        raise web.HTTPNotFound(content_type='application/json', body=json.dumps({'error': 'User not found'}))
    # generate token
    expiration_time = datetime.utcnow() + timedelta(hours=24)
    token = jwt.encode(payload={'login': user['login'],
                                'user_id': user['user_id'],
                                'exp': expiration_time,
                                'aud': 'restore_password_url'},
                       key=request.app['config']['SECRET_KEY']).decode('utf-8')
    # generate url
    url = '{scheme}://{host}/api/v1/restorepassword/{token}'.format(scheme=request.scheme,
                                                                    host=request.app['config']['HOST'] or request.host,
                                                                    token=token)
    data = {'email_type': 'restore_password',
            'to_name': user['login'],
            'to_addr': user['email'],
            'linc': url,
            'subject': 'Restore Password'}
    '''
    email = Email(request)
    email_resp = await email.send(request.scheme, request.app['config']['EMAIL_SERVICE_HOST'], data={'email_type': 'restore_password',
                                                                                                     'to_name': user['login'],
                                                                                                     'to_addr': user['email'],
                                                                                                     'linc': url,
                                                                                                     'subject': 'Restore Password'})

    if not email_resp['success']:
        raise web.HTTPUnprocessableEntity(content_type='application/json', body=json.dumps({'email_service_error': email_resp['error']}))
    '''

    # await request.app.rmq.produce(data, request.app['config']['RMQ_PRODUCER_QUEUE'])
    await request.app.redis.rpush('email', json.dumps(data))

    return web.Response(status=200, content_type='application/json', body=json.dumps({'status': 'ok'}))


@swagger_path('swagger/restore_password_get.yaml')
@auth_routes.get('/api/v1/restorepassword/{token}')
async def restore_password_confirmation(request: web.Request) -> web.Response:
    token = request.match_info['token']
    user = token_decode(token, request.app['config']['SECRET_KEY'], 'restore_password_url')

    return await set_authorization_coockie(user, {'minutes': 5}, request.app['config']['SECRET_KEY'], audience='restore_password_coockie')


@swagger_path('swagger/password_new.yaml')
@auth_routes.post('/api/v1/user/password/new')
@serialize_body('reset_password')
async def reset_password(request: web.Request, body) -> web.Response:
    token = request.cookies.get('AppCoockie')

    if not token:
        raise web.HTTPForbidden(body=json.dumps({'error': 'Access denied for requested resource'}),
                                content_type='application/json')
    
    user = token_decode(token, request.app['config']['SECRET_KEY'], audience='restore_password_coockie')
    user_table = get_model_by_name('user')
    user_exists = await request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user['user_id'])]))
    
    if not user_exists:
        raise web.HTTPNotFound(
            body=json.dumps({'error': 'User not found'}),
            content_type='application/json')
    
    user = await request.app['pg'].fetchrow(user_table.update().where(
        user_table.c.user_id == user['user_id']).values(**body).returning(literal_column('*')))

    if request.app['config']['AUTO_AUTHENTICATION']:
        return await set_authorization_coockie(user, {'hours': 24}, request.app['config']['SECRET_KEY'])
    
    return web.Response(body=json.dumps({'status': 'ok'}), content_type='application/json')
