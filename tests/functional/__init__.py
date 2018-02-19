import os
import sys
import asyncio

from aiohttp.test_utils import AioHTTPTestCase

path_to_application = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), './../../'))
sys.path.insert(0, path_to_application)

from app.app import create_app
from app.utils import get_test_config, migrate, drop_tables


class TestCase(AioHTTPTestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.config = get_test_config()
        self.app = self.loop.run_until_complete(self.get_application())
        self.server = self.loop.run_until_complete(self.get_server(self.app))
        self.client = self.loop.run_until_complete(
            self.get_client(self.server))

        self.loop.run_until_complete(self.client.start_server())

        self.loop.run_until_complete(self.setUpAsync())

        migrate(self.config, silent=True)

    def tearDown(self):
        self.loop.run_until_complete(drop_tables(self.config))
        super().tearDown()

    async def get_application(self):
        return create_app(self.config)