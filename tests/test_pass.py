import pytest
from fleets.db import get_db
from werkzeug.security import check_password_hash

def test_pass_get_user(client, auth):
    auth.login_user()
    with client:
        assert client.get('/password').status_code == 200

def test_pass_get_admin(client, auth):
    auth.login_admin()
    with client:
        assert client.get('/password').status_code == 200

def test_pass_get_owner(client, auth):
    auth.login_owner()
    with client:
        assert client.get('/password').status_code == 200


@pytest.mark.parametrize(('old', 'password', 'confirmation', 'message'), (
    ('', '', '', b"Must provide Old-password"),
    ('a', '', '', b"Must provide Password"),
    ('a', 'a', '', b"Must provide Confirmation"),
    ('a', 'a', 'a', b"Wrong password"),
    ('test', 'a', 'b', b"Password and confimation don&#39;t match"),
    ('test', 'a', 'a', b"Password changed!"),
))
def test_pass_post_admin(client, auth, old, password, confirmation, message, app):
    auth.login_admin()
    with client:
        response = client.post(
            '/password', data = {'old-password': old, 'password': password, 'confirmation': confirmation},
            follow_redirects=True,
        )
        
        assert message in response.data

        if message == b"Password changed!":
            with app.app_context():

                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'test'",
                ).fetchone()
                assert check_password_hash(u["hash"], password)
        else:
            with app.app_context():
                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'test'",
                ).fetchone()
                assert not check_password_hash(u["hash"], password)

@pytest.mark.parametrize(('old', 'password', 'confirmation', 'message'), (
    ('', '', '', b"Must provide Old-password"),
    ('a', '', '', b"Must provide Password"),
    ('a', 'a', '', b"Must provide Confirmation"),
    ('a', 'a', 'a', b"Wrong password"),
    ('kk', 'a', 'b', b"Password and confimation don&#39;t match"),
    ('kk', 'a', 'a', b"Password changed!"),
))
def test_pass_post_owner(client, auth, old, password, confirmation, message, app):
    auth.login_owner()
    with client:
        response = client.post(
            '/password', data = {'old-password': old, 'password': password, 'confirmation': confirmation},
            follow_redirects=True,
        )
        print(response.data)
        assert message in response.data

        if message == b"Password changed!":
            with app.app_context():

                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'Angel'",
                ).fetchone()
                assert check_password_hash(u["hash"], password)
        else:
            with app.app_context():
                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'Angel'",
                ).fetchone()
                assert not check_password_hash(u["hash"], password)

@pytest.mark.parametrize(('old', 'password', 'confirmation', 'message'), (
    ('', '', '', b"Must provide Old-password"),
    ('a', '', '', b"Must provide Password"),
    ('a', 'a', '', b"Must provide Confirmation"),
    ('a', 'a', 'a', b"Wrong password"),
    ('test', 'a', 'b', b"Password and confimation don&#39;t match"),
    ('test', 'a', 'a', b"Password changed!"),
))
def test_pass_post_user(client, auth, old, password, confirmation, message, app):
    auth.login_user()
    with client:
        response = client.post(
            '/password', data = {'old-password': old, 'password': password, 'confirmation': confirmation},
            follow_redirects=True,
        )
        
        assert message in response.data

        if message == b"Password changed!":
            with app.app_context():

                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'test2'",
                ).fetchone()
                assert check_password_hash(u["hash"], password)
        else:
            with app.app_context():
                u = get_db().execute(
                    "SELECT * FROM users WHERE username = 'test2'",
                ).fetchone()
                assert not check_password_hash(u["hash"], password)