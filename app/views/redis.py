import json
import asyncio

import aioredis


async def listen_to_redis(app):
    try:
        print('Redis wait for message')
        while True:
            if not bool(await app.redis.llen('email_response')):
                continue

            message_data = await app.redis.lpop('email_response')

            if not message_data:
                print(message_data)
                continue

            message_data = json.loads(message_data)
            print(message_data)

    except asyncio.CancelledError:
        pass
    except Exception as ex:
        print(ex)
    finally:
        print('Close redis')
        await app.redis.quit()


async def init_redis(app):
    print('init redis')
    app.redis = await aioredis.create_redis(('localhost', 6379), loop=app.loop)
