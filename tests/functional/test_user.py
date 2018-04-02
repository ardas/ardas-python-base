from aiohttp.test_utils import unittest_run_loop

from . import TestCase, AUTH_ERROR
from app.models import User


user_create_data = {'login': 'test_user', 'password': 'test', 'email': 'test@email.com'}
user_check_data = {'login': 'test_user', 'user_id': 1, 'first_name': None, 'last_name': None, 'email': 'test@email.com'}
AUTH_ERROR = {'error': 'Access denied for requested resource'}

class TestUserView(TestCase):

    async def create_user(self, login=None):
        user_data = {
            'login': user_create_data['login'] if not login else login,
            'password': user_create_data['password'],
            'email': user_create_data['email'],
        }
        async with self.app['pg'].transaction() as conn:
            await conn.fetch(User.insert().values(**user_data))

    @unittest_run_loop
    async def test_create_user_200(self):
        response_create = await self.client.session.request('POST', self.client.make_url('/api/v1/users'),
                                                     json=user_create_data)
        
        body = await response_create.json()
        self.assertEqual(response_create.status, 201)
        self.assertEqual(body, {'user_id': 1,
                                'login': 'test_user',
                                'email': 'test@email.com'})

    @unittest_run_loop
    async def test_create_user_with_existing_login(self):
        await self.client.session.request('POST', self.client.make_url('/api/v1/users'),
                                          json=user_create_data)
        response = await self.client.session.request('POST', self.client.make_url('/api/v1/users'),
                                                     json=user_create_data)
        body = await response.json()
        self.assertEqual(response.status, 409)
        self.assertEqual(body, {'error': 'User with login "{}" already exist'.format(user_create_data['login'])})
    
    @unittest_run_loop
    async def test_get_user_200(self):
        await self.create_user()
        user_id = 1
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)

        response_get = await self.client.session.request('GET', self.client.make_url(f'/api/v1/users/{user_id}'))
        body = await response_get.json()
        self.assertEqual(response_get.status, 200)
        self.assertEqual(body, user_check_data)
    
    @unittest_run_loop
    async def test_get_user_403(self):
        await self.create_user()
        user_id = 1

        response_get = await self.client.session.request('GET', self.client.make_url(f'/api/v1/users/{user_id}'))
        body = await response_get.json()

        self.assertEqual(response_get.status, 403)
        self.assertEqual(body, AUTH_ERROR)

    @unittest_run_loop
    async def test_get_all_users(self):
        await self.create_user()

        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)

        response_get = await self.client.session.request('GET', self.client.make_url('/api/v1/users'))
        body = await response_get.json()

        self.assertEqual(response_get.status, 200)
        self.assertEqual(body, [user_check_data])
    
    @unittest_run_loop
    async def test_get_all_users_403(self):
        await self.create_user()

        response_get = await self.client.session.request('GET', self.client.make_url('/api/v1/users'))
        body = await response_get.json()

        self.assertEqual(response_get.status, 403)
        self.assertEqual(body, AUTH_ERROR)
    
    @unittest_run_loop
    async def test_patch_user_200(self):
        await self.create_user()
        user_id = 1
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)

        response_patch = await self.client.session.request('PATCH', self.client.make_url(f'/api/v1/users/{user_id}'),
                                                           json={'first_name': 'test'})
        body = await response_patch.json()
        check = user_check_data.copy()
        check['first_name'] = 'test'
        self.assertEqual(response_patch.status, 200)
        self.assertEqual(body, check)
    
    @unittest_run_loop
    async def test_patch_user_403(self):
        await self.create_user()
        user_id = 1
        response_patch = await self.client.session.request('PATCH', self.client.make_url(f'/api/v1/users/{user_id}'),
                                                           json={'first_name': 'test'})

        body = await response_patch.json()

        self.assertEqual(response_patch.status, 403)
        self.assertEqual(body, AUTH_ERROR)
    
    @unittest_run_loop
    async def test_patch_user_by_another_user(self):
        await self.create_user()
        await self.create_user(login='test_user_2')
        user_id = 2
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)

        response_patch = await self.client.session.request('PATCH', self.client.make_url(f'/api/v1/users/{user_id}'),
                                                           json={'first_name': 'test'})
        body = await response_patch.json()

        self.assertEqual(response_patch.status, 403)
        self.assertEqual(body, AUTH_ERROR)