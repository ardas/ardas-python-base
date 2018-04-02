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
import aioredis

from .routes import setup_routes
from .utils import get_config, connect_to_db
from .middlewares import error_middleware, auth_middleware
from .services.rabbitmq import RabbitConnector
from .views.rabbit import listen_to_rabbit
from .views.redis import listen_to_redis, init_redis

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
middlewares = [error_middleware, auth_middleware]


async def start_background_tasks(app):
    # app['rabbit_listener'] = app.loop.create_task(listen_to_rabbit(app))
    app['redis_listener'] = app.loop.create_task(listen_to_redis(app))


async def cleanup_background_tasks(app):
    # app['rabbit_listener'].cancel()
    # await app['rabbit_listener']
    app['redis_listener'].cancel()
    await app['redis_listener']


def create_app(config=None):
    
    if not config:
        config = get_config()
    
    cpu_count = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()

    if config['DEBUG']:
        middlewares.append(toolbar_middleware_factory)

    app = web.Application(loop=loop, middlewares=middlewares)
    
    if config['DEBUG']:
        aiohttp_debugtoolbar.setup(app)

    app['executor'] = ProcessPoolExecutor(cpu_count)
    app['config'] = config
    # app.rmq = RabbitConnector(app['config'], app.loop)
    # app.loop.run_until_complete(app.rmq.connect(channel_number=2))
    app.on_startup.append(init_database)
    app.on_startup.append(init_redis)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    setup_routes(app)
    setup_swagger(app, swagger_url='/api/v1/doc')

    return app


async def init_database(app):
    app['pg'] = await connect_to_db(app['config'])