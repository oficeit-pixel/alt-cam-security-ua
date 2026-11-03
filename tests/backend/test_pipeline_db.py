"""Opt-in end-to-end pipeline test against a disposable local PostgreSQL (TCP localhost or unix socket)."""
import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path

import asyncpg
import pytest
from sqlalchemy.engine import make_url

SCENARIO = Path(__file__).with_name("pipeline_db_scenario.py")
DISPATCH = Path(__file__).with_name("pipeline_dispatch_scenario.py")


def _local(url) -> bool:
    host = url.host or url.query.get("host", "")
    return host in {"127.0.0.1", "localhost"} or str(host).startswith("/")


@pytest.mark.parametrize("method", ["runtime", "alembic"])
def test_pipeline_end_to_end(method):
    raw = os.environ.get("TEST_PIPELINE_POSTGRES_URL") or os.environ.get("TEST_POSTGRES_URL")
    if not raw:
        pytest.skip("TEST_PIPELINE_POSTGRES_URL / TEST_POSTGRES_URL required (disposable local PostgreSQL)")
    url = make_url(raw)
    assert _local(url), "Production databases are forbidden"
    name = "altcam_pipeline_" + uuid.uuid4().hex[:12]

    async def database(create):
        kwargs = {"host": url.query["host"]} if url.query.get("host") else {}
        conn = await asyncpg.connect(url.set(query={}).render_as_string(hide_password=False).replace("postgresql+asyncpg", "postgresql"), **kwargs) if kwargs else await asyncpg.connect(raw)
        try:
            await conn.execute(f'CREATE DATABASE "{name}"' if create else f'DROP DATABASE "{name}" WITH (FORCE)')
        finally:
            await conn.close()

    asyncio.run(database(True))
    env = dict(os.environ, DATABASE_URL=url.set(database=name).render_as_string(hide_password=False), BOT_TOKEN="",
               ENABLE_BOT_POLLING="false", PORT="0",
               PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    root = Path(__file__).resolve().parents[2]
    try:
        if method == "alembic":
            subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], env=env, cwd=root, check=True)
        result = subprocess.run([sys.executable, str(SCENARIO)], env=env, cwd=root, capture_output=True, text=True, timeout=180)
        assert result.returncode == 0 and "PIPELINE_DB_SCENARIO_OK" in result.stdout, result.stdout[-4000:] + result.stderr[-6000:]
        if method == "runtime":  # real Dispatcher on a fresh database
            asyncio.run(database(False))
            asyncio.run(database(True))
            result = subprocess.run([sys.executable, str(DISPATCH)], env=env, cwd=root, capture_output=True, text=True, timeout=180)
            assert result.returncode == 0 and "PIPELINE_DISPATCH_SCENARIO_OK" in result.stdout, result.stdout[-4000:] + result.stderr[-6000:]
    finally:
        asyncio.run(database(False))
