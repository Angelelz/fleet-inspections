import os
import tempfile

import pytest
from fleets import create_app
from fleets.db import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login_user(self, company='test', username='test2', password='test'):
        return self._client.post(
            '/login',
            data={'company': company, 'username': username, 'password': password}
        )

    def login_admin(self, company='test', username='test', password='test'):
        return self._client.post(
            '/login',
            data={'company': company, 'username': username, 'password': password}
        )

    def login_owner(self, company='test', username='Angel', password='kk'):
        return self._client.post(
            '/login',
            data={'company': company, 'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)