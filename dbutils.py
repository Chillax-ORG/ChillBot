import os

import discord
import json


DB_NAME = 'storage/db.json'


def load_db(guild: discord.Guild | None) -> dict:
    if not guild:
        raise ValueError('Missing guild')
    
    # return this guild's entry in db.json
    db = _load_db()
    _validate_db(guild, db)
    return db[str(guild.id)]


def save_db(guild: discord.Guild | None, data: dict) -> None:
    if not guild:
        raise ValueError('Missing guild')
    
    current_db = _load_db()
    with open(DB_NAME, 'w') as db:
        current_db[str(guild.id)] = data
        json.dump(current_db, db)


def _load_db():
    # load the entire db.json
    if not os.path.isfile(DB_NAME):
        with open(DB_NAME, 'w') as db:
            db.write(json.dumps({}))
    with open(DB_NAME, 'r') as db:
        return json.load(db)


def _validate_db(guild: discord.Guild, db: dict) -> None:
    # Validates db schema, repairing if necessary
    dirty = False
    if str(guild.id) not in db or 'enabled_channel' not in db[str(guild.id)]:
        db[str(guild.id)] = {'enabled_channel': -1}
        dirty = True
    elif not isinstance(db[str(guild.id)]['enabled_channel'], int):
        db[str(guild.id)]['enabled_channel'] = -1
        dirty = True

    if dirty:
        save_db(guild, db[str(guild.id)])
