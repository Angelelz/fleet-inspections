import pytest
from flask import g, session
from fleets.db import get_db


def test_register(client, app):
    assert client.get('/register').status_code == 200
    response = client.post(
        '/register', data={'company': 'a', 'username': 'a', 'email': 'a', 'password': 'a', 'confirmation': 'a'},
        follow_redirects=True
    )
    assert response.headers['Set-Cookie'].endswith("=/")
    

    with app.app_context():
        assert get_db().execute(
            "SELECT * FROM users WHERE username = 'a'",
        ).fetchone() is not None


@pytest.mark.parametrize(('company', 'username', 'email', 'password', 'confirmation', 'message'), (
    ('', '', '', '', '', b"Company field cannot be empty"),
    ('a', '', '', '', '', b"Username field cannot be empty"),
    ('a', 'a', '', '', '', b"Email field cannot be empty"),
    ('a', 'a', 'a', '', '', b"Password field cannot be empty"),
    ('a', 'a', 'a', 'a', '', b"Confirmation field cannot be empty"),
    ('test', 'test', 'test', 'test', 'test', b'Company name already exists'),
))
def test_register_validate_input(client, company, username, email, password, confirmation, message):
    response = client.post(
        '/register',
        data={'company': company, 'username': username, 'email': email, 'password': password, 'confirmation': confirmation},
        follow_redirects=True
    )
    assert message in response.data

def test_login(client, auth):
    assert client.get('/login').status_code == 200
    response = auth.login_user()
    assert response.headers['Location'] == 'http://localhost/'

    with client:
        client.get('/')
        assert session['user_id'] == 4
        assert g.user['username'] == 'test2'


@pytest.mark.parametrize(('company', 'username', 'password', 'message'), (
    ('', '', '', b'Must provide Company'),
    ('a', '', '', b'Must provide Username'),
    ('a', 'a', '', b'Must provide Password'),
    ('a', 'a', 'a', b'Company not found'),
    ('test', 'a', 'a', b'Invalid username and/or password'),
))
def test_login_validate_input(auth, company, username, password, message):
    response = auth.login_user(company, username, password)
    assert message in response.data

def test_logout(client, auth):
    auth.login_user()

    with client:
        auth.logout()
        assert 'user_id' not in session