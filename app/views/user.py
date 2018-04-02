import json

from aiohttp import web, ClientSession
from sqlalchemy import literal_column, select, exists
from aiohttp_swagger import *

from app.models import get_model_by_name, row_to_dict
from app.services.serializers import serialize_body, id_validator

@swagger_path('swagger/create_user.yaml')
@serialize_body('user_schema')
async def create_user(request: web.Request, body) -> web.Response:
    user_table = get_model_by_name('user')
    login = body['login']
    exist = await request.app['pg'].fetchval(select([exists().where(user_table.c.login == login)]))

    if exist:
        return web.HTTPConflict(body=json.dumps({'error': f'User with login "{login}" already exist'}), content_type='application/json')

    data = await request.app['pg'].fetchrow(user_table.insert().values(**body).returning(literal_column('*')))
    body['user_id'] = data['user_id']
    del body['password']

    return web.Response(
        status=201, content_type='application/json', body=json.dumps(body))

@swagger_path('swagger/get_all_users.yaml')
async def get_all_users(request: web.Request) -> web.Response:
    user_table = get_model_by_name('user')
    users = await request.app['pg'].fetch(user_table.select())
    result = [row_to_dict(user_table, user) for user in users]

    return web.Response(status=200, content_type='application/json',
                        body=json.dumps(result))


@swagger_path('swagger/get_user.yaml')
async def get_user(request: web.Request) -> web.Response:
    user_id = id_validator(request.match_info['user_id'], 'user')
    user_table = get_model_by_name('user')
    user_exists = await request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

    if not user_exists:
        raise web.HTTPNotFound(
            body=json.dumps({'error': f'User with id={user_id} not found'}),
            content_type='application/json')

    user = await request.app['pg'].fetchrow(
        user_table.select().where(user_table.c.user_id == user_id))
    
    return web.Response(status=200, content_type='application/json',
                        body=json.dumps(row_to_dict(user_table, user)))

@swagger_path('swagger/patch_user.yaml')
@serialize_body('patch_user_schema')
async def patch_user(request: web.Request, body) -> web.Response:
    user_id = id_validator(request.match_info['user_id'], 'user')
    user_table = get_model_by_name('user')
    user_exists = await request.app['pg'].fetchval(select([exists().where(user_table.c.user_id == user_id)]))

    if not user_exists:
        raise web.HTTPNotFound(
            body=json.dumps({'error': f'User with id={user_id} not found'}),
            content_type='application/json')
    
    if request.auth_user['user_id'] != user_id:
        raise web.HTTPForbidden(body=json.dumps({'error': 'Access denied for requested resource'}),
                                   content_type='application/json')
    
    if not body:
        return web.Response(status=200, content_type='application/json',
                            body=json.dumps({}))

    user = await request.app['pg'].fetchrow(user_table.update().where(
        user_table.c.user_id == user_id).values(**body).returning(literal_column('*')))
    
    result = row_to_dict(user_table, user)

    return web.Response(status=200, content_type='application/json',
                        body=json.dumps(result))





