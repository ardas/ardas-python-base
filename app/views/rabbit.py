import json
import asyncio

from pika.exceptions import ChannelClosed


async def listen_to_rabbit(app):
    try:
        consume_queue = await app.rmq.declare_queue(app['config']['RMQ_CONSUME_QUEUE'], durable=False)
        print('[*] Waiting for messages. To exit press CTRL+C')
        async for message in consume_queue:
            try:
                print('New message')
                message_data = json.loads(message.body.decode())
                print(message_data)
                print('affter')
                message.ack()
                print('accept message')
            except ChannelClosed:
                pass
            except Exception as ex:
                message.reject(requeue=True)
    except (asyncio.CancelledError, KeyboardInterrupt):
        await app.rmq.close()
    except Exception as ex:
        import ipdb; ipdb.set_trace()
        await listen_to_rabbit(app)