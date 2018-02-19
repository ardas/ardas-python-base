import asyncio
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from aiohttp import web
from aiohttp_swagger import *
import uvloop
import aiohttp_debugtoolbar
from aiohttp_debugtoolbar import toolbar_middleware_factory
from aiohttp_security import setup as setup_security
from aiohttp_security import SessionIdentityPolicy

from .routes import setup_routes
from .utils import get_config, connect_to_db
from .middlewares import error_middleware, auth_middleware

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

def create_app(config=None):
    
    if not config:
        config = get_config()
    
    cpu_count = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop, middlewares=[toolbar_middleware_factory, error_middleware, auth_middleware])
    aiohttp_debugtoolbar.setup(app)
    app['executor'] = ProcessPoolExecutor(cpu_count)
    app['config'] = config
    app.on_startup.append(init_database)
    setup_routes(app)
    setup_swagger(app, swagger_url='/api/v1/doc')

    return app


async def init_database(app):
    app['pg'] = await connect_to_db(app['config'])