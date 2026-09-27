import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest

spec = importlib.util.spec_from_file_location('migration', Path(__file__).resolve().parents[2] / 'scripts/migrate_render_to_neon.py')
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def test_missing_source_skips(monkeypatch):
    monkeypatch.delenv('OLD_DATABASE_URL', raising=False)
    assert migration.main() == 0


def test_confirmation_required(monkeypatch):
    monkeypatch.setenv('OLD_DATABASE_URL','postgresql://old/db')
    monkeypatch.setenv('NEW_DATABASE_URL','postgresql://new/db')
    monkeypatch.delenv('CONFIRM_NEON_RESTORE',raising=False)
    with pytest.raises(RuntimeError,match='CONFIRM_NEON_RESTORE'): migration.main()


def test_credentials_only_in_environment(monkeypatch):
    def run(args, **kwargs):
        assert all('secret' not in arg for arg in args)
        assert kwargs['env']['PGDATABASE'] == 'postgresql://u:secret@host/db?sslmode=require'
        assert 'OLD_DATABASE_URL' not in kwargs['env']
        return SimpleNamespace(returncode=1,stdout='',stderr='secret url error')
    monkeypatch.setattr(migration.subprocess,'run',run)
    with pytest.raises(RuntimeError) as result:
        migration.run('psql','postgresql+asyncpg://u:secret@host/db?ssl=require')
    assert 'secret' not in str(result.value)
