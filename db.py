import sqlite3
from flask import g

DATABASE = "flagada.db"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS flags (
            value            TEXT PRIMARY KEY,
            application_name TEXT NOT NULL,
            description      TEXT,
            status           TEXT NOT NULL DEFAULT 'NOT_FOUND_YET',
            owner            TEXT NOT NULL DEFAULT 'NA',
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()
