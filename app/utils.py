import argparse
import os
import yaml
import logging
import json

# from trafaret_config import commandline
# import trafaret
import asyncpg
from asyncpgsa import pg, PG
from sqlalchemy.engine.default import StrCompileDialect
import alembic.config as alembic_config
import alembic.command as alembic_command

VERIABLES = ['VERSION']

# TRAFARET = trafaret.Dict({'version': trafaret.String()})

# def load_config(app):
#     ap = argparse.ArgumentParser()
#     import ipdb; ipdb.set_trace()

#     commandline.standard_argparse_options(ap, default_config='./config/app.yaml')
#     options = ap.parse_args()
#     config = commandline.config_from_options(options, TRAFARET)
#     app['config'] = config
#     return app


def get_test_config():
    config = get_config()
    config['DB_NAME'] = 'test_database'
    config['PROD'] = False
    config['HOST'] = None
    config['TEST_ENV'] = True
    return config


def load_config(file_path):
    with open(file_path, 'r') as conf_file:
        config = yaml.load(conf_file)
    return config


def get_config():
    log = logging.getLogger()
    config = {}
    try:
        config = load_config(os.path.join(os.path.dirname(os.path.realpath(__file__)), './../config/app.yaml'))
    except FileNotFoundError:
        pass
    except yaml.YAMLError:
        log.error('Failed to load config, incorrect format. Trying to load from ENV variables')

    config.update(_load_from_env(VERIABLES))
    return config


def _load_from_env(keys):
    env_config = {}

    for key in keys:
        env_value = os.environ.get(key)

        if env_value:
            env_config[key] = env_value

    return env_config


class JSONCompileDialect(StrCompileDialect):
    def _json_serializer(self, value):
        return json.dumps(value)

    def _json_deserializer(self, value):
        return json.loads(value)


async def connect_to_db(config: dict) -> PG:
    await pg.init(database=config['DB_NAME'],
                  host=config['DB_HOST'],
                  port=config['DB_PORT'],
                  user=config['DB_USER'],
                  password=config['DB_PASSWORD'],
                  dialect=JSONCompileDialect())
    return pg


async def create_database(config):
    conn = await connect_to_postgres(config)

    try:
        await conn.fetch('CREATE DATABASE {}'.format(config['DB_NAME']))
    except asyncpg.DuplicateDatabaseError:
        print('Database {} already exists'.format(config['DB_NAME']))
        #sys.exit(1)


async def drop_tables(config):
    conn = await connect_to_db(config)
    await conn.fetch('''DROP schema public cascade;''')
    await conn.fetch('''CREATE schema public;''')


async def connect_to_postgres(config: dict) -> PG:
    await pg.init(database='postgres',
                  host=config['DB_HOST'],
                  port=config['DB_PORT'],
                  user=config['DB_USER'],
                  password=config['DB_PASSWORD'],
                  dialect=JSONCompileDialect())
    return pg


async def drop_database(config):
    conn = await connect_to_postgres(config)

    try:
        await conn.fetch('''
SELECT pg_terminate_backend(pg_stat_activity.pid) 
FROM pg_stat_activity 
WHERE pg_stat_activity.datname = '{}' AND pid <> pg_backend_pid();
'''.format(config['DB_NAME']))
        await conn.fetch('DROP DATABASE {}'.format(config['DB_NAME']))
    except asyncpg.InvalidCatalogNameError:
        print('Database {} does not exists'.format(config['DB_NAME']))


def migrate(config, silent=False):
    sqlalchemy_url = 'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}' \
        .format(**config)

    alembic_cfg = alembic_config.Config('alembic.ini')
    alembic_cfg.set_main_option(name='sqlalchemy.url', value=sqlalchemy_url)

    if silent:
        alembic_cfg.set_main_option(name='silent', value='true')

    alembic_command.upgrade(alembic_cfg, 'head')
