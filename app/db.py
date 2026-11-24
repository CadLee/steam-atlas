import json
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb, set_json_loads

from app.config import SCHEMA_PATH, database_url


def parse_json(value):
    if isinstance(value, str):
        return json.loads(value)
    return value


def connect():
    conn = psycopg.connect(database_url(), row_factory=dict_row)
    set_json_loads(json.loads, conn)
    return conn


@contextmanager
def transaction():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    script = SCHEMA_PATH.read_text()
    with connect() as conn:
        conn.execute(script)
        conn.commit()


def jsonb(value):
    return Jsonb(value)
