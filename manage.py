#!/usr/bin/env python
from flaskext.script import Manager
from app import app, get_redis

manager = Manager(app)


@manager.command
def flush():
    r = get_redis()
    r.flushdb()

if __name__ == "__main__":
    manager.run()
