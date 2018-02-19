from aiohttp.test_utils import unittest_run_loop
from aiohttp import web

from . import TestCase

class TestVersionView(TestCase):

    @unittest_run_loop
    async def test_version(self):
        request = await self.client.request("GET", "/api/version")
        assert request.status == 200
        text = await request.json() 
        assert 'version' in text