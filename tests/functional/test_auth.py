from aiohttp.test_utils import unittest_run_loop

from . import TestCase, AUTH_ERROR
from app.models import User

user_create_data = {'login': 'test_user', 'password': 'test'}
login_error = {'error': 'Invalid username / password combination'}

class TestAuthView(TestCase):

    async def create_user(self):
        async with self.app['pg'].transaction() as conn:
            await conn.fetch(User.insert().values(**user_create_data))
    
    @unittest_run_loop
    async def test_login_200(self):
        await self.create_user()
        user_id = 1
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                    json=user_create_data)
        self.assertEqual(response_login.status, 200)
        body = await response_login.json()
        self.assertEqual(body, {'user_id': user_id})
    
    @unittest_run_loop
    async def test_login_wrong_data(self):
        await self.create_user()
        user_id = 1
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                                                        json={'login': 'wrong', 'password': 'super_wrong'})
        self.assertEqual(response_login.status, 401)
        body = await response_login.json()
        self.assertEqual(body, login_error)
    
    @unittest_run_loop
    async def test_logout_200(self):
        await self.create_user()
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)
        response_logout = await self.client.session.request('GET', self.client.make_url('/api/v1/auth/logout'))
        self.assertEqual(response_logout.status, 200)
        body = await response_logout.json()
        self.assertEqual(body, {'status': 'Ok'})
    
    @unittest_run_loop
    async def test_logout_403(self):
        response_logout = await self.client.session.request('GET', self.client.make_url('/api/v1/auth/logout'))
        self.assertEqual(response_logout.status, 403)
        body = await response_logout.json()
        self.assertEqual(body, AUTH_ERROR)