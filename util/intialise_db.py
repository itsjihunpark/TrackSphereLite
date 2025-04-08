import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

def make_connection():
    db = sqlite3.connect(
        "../instance/piTrackSphere.sqlite",
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    return db

def init_db():
    db = make_connection()
    with open('./schema.sql') as f:
        db.executescript(f.read())

def populate_with_dummy_data():
    db = make_connection()
    with open('./populate_dummy_data.sql') as f:
        db.executescript(f.read())

if __name__ == "__main__":
    init_db()
    #populate_with_dummy_data()
else:
    pass