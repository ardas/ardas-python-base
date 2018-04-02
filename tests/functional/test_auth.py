from aiohttp.test_utils import unittest_run_loop, make_mocked_request
from aiohttp import web
from unittest.mock import patch, Mock, call
from sqlalchemy import select

from . import TestCase, AUTH_ERROR
from app.models import User

user_create_data = {'login': 'test_user', 'password': 'test', 'email': 'test@email.com'}
login_error = {'error': 'Invalid username / password combination'}


class TestAuthView(TestCase):

    async def create_user(self):
        async with self.app['pg'].transaction() as conn:
            await conn.fetch(User.insert().values(**user_create_data))

    @unittest_run_loop
    async def test_login_200(self):
        await self.create_user()
        response_login = await self.client.session.request('POST', self.client.make_url('/api/v1/auth/login'),
                                                           json=user_create_data)
        self.assertEqual(response_login.status, 200)
        body = await response_login.json()
        self.assertEqual(body, {'status': 'ok'})

    @unittest_run_loop
    async def test_login_wrong_data(self):
        await self.create_user()
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
        self.assertEqual(body, {'status': 'ok'})

    @unittest_run_loop
    async def test_logout_403(self):
        response_logout = await self.client.session.request('GET', self.client.make_url('/api/v1/auth/logout'))
        self.assertEqual(response_logout.status, 403)
        body = await response_logout.json()
        self.assertEqual(body, AUTH_ERROR)


class TestRestoreUserPasswordView(TestCase):
    async def create_user(self):
        async with self.app['pg'].transaction() as conn:
            await conn.fetch(User.insert().values(**user_create_data))

    @unittest_run_loop
    async def test_forgot_password(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                                                       json={'login': user_create_data['login']})
        data = await response_post.json()
        self.assertEqual(response_post.status, 200)
        self.assertTrue(data['success'])

    @unittest_run_loop
    async def test_forgot_password_404(self):
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                                                       json={'login': user_create_data['login']})
        data = await response_post.json()
        self.assertEqual(response_post.status, 404)
        self.assertTrue(data, {'error': 'User not found'})
    
    @unittest_run_loop
    async def test_forgot_password_wrong_data(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                          json={'wrong': 'superwrong'})
        data = await response_post.json()
        self.assertEqual(response_post.status, 422)
        self.assertEqual(data, {'login': ['Missing data for required field.']})

    @unittest_run_loop
    async def test_restore_password_confirmation(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                                                       json={'login': user_create_data['login']})
        self.assertEqual(response_post.status, 200)
        data = await response_post.json()
        url = data['data']['linc']
        response_get = await self.client.session.request('GET', url)
        data = await response_get.json()
        self.assertEqual(response_get.status, 200)
        self.assertEqual(data, {'status': 'ok'})
    
    @unittest_run_loop
    async def test_restore_password_confirmation_wrong_token(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                                                       json={'login': user_create_data['login']})
        self.assertEqual(response_post.status, 200)
        data = await response_post.json()
        url = data['data']['linc']
        response_get = await self.client.session.request('GET', url[:-1])
        data = await response_get.json()
        self.assertEqual(response_get.status, 401)
        self.assertEqual(data, {'error': 'Invalid token'})
    
    @unittest_run_loop
    async def test_reset_password(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                          json={'login': user_create_data['login']})
        self.assertEqual(response_post.status, 200)
        data = await response_post.json()
        url = data['data']['linc']
        response_get = await self.client.session.request('GET', url)
        self.assertEqual(response_get.status, 200)
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/user/password/new'),
                                                          json={'password': 'newtestpassword'})
        data = await response_post.json()
        user_password = await self.app['pg'].fetchval(select([User.c.password]).where(User.c.user_id == 1))

        self.assertEqual(response_post.status, 200)
        self.assertEqual(data, {'status': 'ok'})
        self.assertEqual(user_password, 'newtestpassword')
    
    @unittest_run_loop
    async def test_reset_password_403(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                          json={'login': user_create_data['login']})
        self.assertEqual(response_post.status, 200)
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/user/password/new'),
                                                          json={'password': 'newtestpassword'})
        data = await response_post.json()

        self.assertEqual(response_post.status, 403)
        self.assertEqual(data, {'error': 'Access denied for requested resource'})

    @unittest_run_loop
    async def test_reset_password_wrong_data(self):
        await self.create_user()
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/restorepassword'),
                                                          json={'login': user_create_data['login']})
        self.assertEqual(response_post.status, 200)
        data = await response_post.json()
        url = data['data']['linc']
        response_get = await self.client.session.request('GET', url)
        self.assertEqual(response_get.status, 200)
        response_post = await self.client.session.request('POST', self.client.make_url('/api/v1/user/password/new'),
                                                          json={'wrong': 'superwrong'})
        data = await response_post.json()

        self.assertEqual(response_post.status, 422)
        self.assertEqual(data, {'password': ['Missing data for required field.']})
