import json

import jwt
from jwt.exceptions import ExpiredSignatureError, DecodeError, InvalidAudienceError
from aiohttp import web

from app.services.serializers import InvalidParameterException
from app.services.auth import check_public_resources


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    # except web.HTTPNotFound as exc:
    #     raise web.HTTPNotFound(body=json.dumps({'error': str(exc)}), content_type='application/json')
    except InvalidParameterException as exc:
        raise web.HTTPUnprocessableEntity(body=json.dumps({'error': str(exc)}),
                                          content_type='application/json')


@web.middleware
async def auth_middleware(request, handler):
    if check_public_resources(request.path, request.method):
        return await handler(request)

    token = request.cookies.get('AppCoockie')

    if not token:
        raise web.HTTPForbidden(body=json.dumps({'error': 'Access denied for requested resource'}),
                                content_type='application/json')
                            
    try:
        data = jwt.decode(token, key=request.app['config']['SECRET_KEY'])
    except ExpiredSignatureError:
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Token expired'}),
                                    content_type='application/json')
    except (InvalidAudienceError, DecodeError):
        raise web.HTTPUnauthorized(body=json.dumps({'error': 'Invalid token'}),
                                   content_type='application/json')

    request.auth_user = {'login': data['login'], 'user_id': data['user_id']}

    return await handler(request)


