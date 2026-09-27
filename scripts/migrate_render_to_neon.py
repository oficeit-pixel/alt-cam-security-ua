"""Manual, offline migration using libpq tools. Never print connection strings."""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def libpq_url(value):
    parts = urlsplit(value.replace('postgresql+asyncpg://', 'postgresql://', 1))
    query = dict(parse_qsl(parts.query))
    if 'ssl' in query:
        query['sslmode'] = query.pop('ssl')
    return urlunsplit(parts._replace(query=urlencode(query)))


def run(tool, url, *args, sql=None):
    env = os.environ.copy()
    for name in ('OLD_DATABASE_URL', 'NEW_DATABASE_URL', 'PGPASSWORD', 'PGSERVICE', 'PGOPTIONS'):
        env.pop(name, None)
    env['PGDATABASE'] = libpq_url(url)
    env['PGCONNECT_TIMEOUT'] = '15'
    result = subprocess.run([tool, *args], input=sql, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{tool} failed (exit {result.returncode}); details suppressed to protect credentials')
    return result.stdout.strip()


COUNTS = """
CREATE TEMP TABLE migration_counts (name text, n bigint);
DO $$ DECLARE r record; n bigint; BEGIN
 FOR r IN SELECT schemaname, tablename FROM pg_tables
 WHERE schemaname NOT IN ('pg_catalog','information_schema') AND schemaname NOT LIKE 'pg_temp%%'
 LOOP
  EXECUTE format('SELECT count(*) FROM %I.%I',r.schemaname,r.tablename) INTO n;
  INSERT INTO migration_counts VALUES (format('%I.%I',r.schemaname,r.tablename),n);
 END LOOP;
END $$;
SELECT coalesce(json_object_agg(name,n),'{}') FROM migration_counts;
"""
SEQUENCES = """
DO $$ DECLARE r record; seq text; highest bigint; first_value bigint; BEGIN
 FOR r IN SELECT c.table_schema,c.table_name,c.column_name
 FROM information_schema.columns c JOIN information_schema.tables t
 USING(table_schema,table_name)
 WHERE t.table_type='BASE TABLE' AND c.table_schema NOT IN ('pg_catalog','information_schema')
 LOOP
  seq := pg_get_serial_sequence(format('%I.%I',r.table_schema,r.table_name),r.column_name);
  IF seq IS NOT NULL THEN
   EXECUTE format('SELECT max(%I) FROM %I.%I',r.column_name,r.table_schema,r.table_name) INTO highest;
   SELECT seqstart INTO first_value FROM pg_sequence WHERE seqrelid=seq::regclass;
   PERFORM setval(seq::regclass,coalesce(highest,first_value),highest IS NOT NULL);
  END IF;
 END LOOP;
END $$;
"""


def counts(url):
    return json.loads(run('psql', url, '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', sql=COUNTS))


def main():
    old, new = os.environ.get('OLD_DATABASE_URL'), os.environ.get('NEW_DATABASE_URL')
    if not old or not new:
        print('SKIPPED: set OLD_DATABASE_URL and NEW_DATABASE_URL to migrate existing data.')
        return 0
    if libpq_url(old) == libpq_url(new):
        raise RuntimeError('Source and destination must differ')
    if os.environ.get('CONFIRM_NEON_RESTORE') != 'YES':
        raise RuntimeError('Restore replaces target tables. Set CONFIRM_NEON_RESTORE=YES only after backing up the target.')
    for tool in ('pg_dump', 'pg_restore', 'psql'):
        if not shutil.which(tool): raise RuntimeError(f'Install PostgreSQL 17 client tools: {tool} is missing')
    source = counts(old)  # Fail before touching the target if Render is suspended.
    run('psql', new, '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', sql='SELECT 1;')
    with tempfile.TemporaryDirectory(prefix='altcam-db-') as directory:
        dump = str(Path(directory) / 'database.dump')
        run('pg_dump', old, '--no-owner', '--no-privileges', '--format=custom', '--file', dump)
        run('pg_restore', new, '--dbname', '', '--no-owner', '--no-privileges',
            '--clean', '--if-exists', '--exit-on-error', '--single-transaction', dump)
        run('psql', new, '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', sql=SEQUENCES)
    target = counts(new)
    print('TABLE\tRENDER\tNEON\tRESULT')
    for table in sorted(source.keys() | target.keys()):
        print(f'{table}\t{source.get(table, "missing")}\t{target.get(table, "missing")}\t'
              f'{"OK" if source.get(table) == target.get(table) else "MISMATCH"}')
    if source != target: raise RuntimeError('Row counts differ; keep writes stopped and investigate')
    print('Migration verified; sequences synchronized. Remove migration environment variables.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        # Do not print unexpected exception messages which might contain URLs.
        print(str(error) if type(error) is RuntimeError else 'Migration failed; sensitive error details suppressed.')
        raise SystemExit(1)
