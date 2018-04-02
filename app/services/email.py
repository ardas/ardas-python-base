import json

from aiohttp import ClientSession, web


class Email:
    def __init__(self, request):
        self.request = request

    async def send(self, scheme: str, host: str, data: dict):

        if self.request.app['config']['TEST_ENV']:
            return {'success': True, 'data': data}

        async with ClientSession() as session:
            async with session.post(f'{scheme}://{host}/api/v1/emails', json=data) as resp:
                body = await resp.json()
                return body
