from aiohttp.test_utils import unittest_run_loop

from . import TestCase



class TestUserView(TestCase):

    @unittest_run_loop
    async def test_create_user_200(self):
        response = await self.client.session.request('POST', self.client.make_url('/api/v1/users'),
                                                     json={'login': 'test_user', 'password': 'test'})
        
        body = await response.json()
        self.assertEqual(response.status, 201)
        self.assertEqual(body, {'id': 1,
                                'login': 'test_user'})
