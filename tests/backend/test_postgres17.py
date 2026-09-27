"""Opt-in integration test; only a disposable localhost PostgreSQL is accepted."""
import asyncio
import os
import subprocess
import sys
import uuid
import asyncpg
import pytest
from sqlalchemy.engine import make_url


@pytest.mark.parametrize('method', ['runtime', 'alembic'])
def test_empty_postgres17(method):
    raw = os.environ.get('TEST_POSTGRES_URL')
    if not raw: pytest.skip('TEST_POSTGRES_URL required (disposable local PostgreSQL 17)')
    url = make_url(raw)
    assert url.host in {'127.0.0.1','localhost'}, 'Production databases are forbidden'
    name = 'altcam_test_' + uuid.uuid4().hex
    async def database(create):
        conn = await asyncpg.connect(raw)
        try:
            assert (await conn.fetchval('SHOW server_version')).startswith('17.')
            await conn.execute(f'CREATE DATABASE "{name}"' if create else f'DROP DATABASE "{name}" WITH (FORCE)')
        finally: await conn.close()
    asyncio.run(database(True))
    env = dict(os.environ, DATABASE_URL=url.set(database=name).render_as_string(hide_password=False), SCHEMA_METHOD=method)
    code = '''
import asyncio, json, os
from sqlalchemy import inspect
from bot.db.base import Base, engine, create_db_schema
from bot.db import models
from bot.web.site_leads import health
async def check():
 if os.environ['SCHEMA_METHOD'] == 'runtime':
  await create_db_schema()
  await create_db_schema()
 async with engine.connect() as c:
  tables = await c.run_sync(lambda s: inspect(s).get_table_names())
  assert set(Base.metadata.tables) <= set(tables)
  for table in Base.metadata.sorted_tables:
   columns = await c.run_sync(lambda s: inspect(s).get_columns(table.name))
   assert set(table.columns.keys()) <= {v['name'] for v in columns}
 assert json.loads((await health(None)).text) == {'ok': True, 'db': True}
 await create_db_schema()
 await engine.dispose()
asyncio.run(check())
'''
    try:
        if method == 'alembic':
            subprocess.run([sys.executable,'-m','alembic','upgrade','head'],env=env,check=True)
        subprocess.run([sys.executable,'-c',code],env=env,check=True)
    finally: asyncio.run(database(False))
