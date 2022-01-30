import pytest
from fleets.db import get_db


def test_index(client):
    response = client.get('/')
    assert b"Log In" in response.data
    assert b"Register" in response.data

def test_index_user(client, auth):
    auth.login_user()
    response = client.get('/')
    assert b'Add User' not in response.data
    assert b'Edit user' not in response.data
    assert b'Users' not in response.data
    assert b'Add Vehicle' in response.data
    assert b'Edit Vehicle' in response.data
    auth.logout()

def test_index_admin(client, auth):
    auth.login_admin()
    response = client.get('/')
    print(response.data)
    assert b'Add User' in response.data
    assert b'Edit User' in response.data
    assert b'Users' in response.data
    assert b'Add Vehicle' in response.data
    assert b'Edit Vehicle' in response.data
    auth.logout()

def test_index_owner(client, auth):
    auth.login_admin()
    response = client.get('/')
    print(response.data)
    assert b'Add User' in response.data
    assert b'Edit User' in response.data
    assert b'Users' in response.data
    assert b'Add Vehicle' in response.data
    assert b'Edit Vehicle' in response.data

def test_add_edit_user_user(client, auth):
    auth.login_user()
    with client:
        assert client.get('/add-user').status_code == 302
        assert client.get('/edit-user').status_code == 302

def test_add_edit_user_admin(client, auth):
    auth.login_admin()
    with client:
        assert client.get('/add-user').status_code == 200
        assert client.get('/edit-user').status_code == 200

def test_add_user_user(client, auth, app):
    auth.login_user()
    with client:
        response = client.get('/add-user')
        assert response.status_code == 302
        assert response.headers['Location'] == "http://localhost/"
        
        response = client.post(
            '/add-user', data={'username': 'a', 'email': 'a', 'password': 'a', 'confirmation': 'a', 'role': 'a'},
        )
        print(response)
        
        assert response.status_code == 302

@pytest.mark.parametrize(('username', 'email', 'password', 'confirmation', 'role', 'message'), (
    ('', '', '', '', '', b"Must provide Username"),
    ('a', '', '', '', '', b"Must provide Email"),
    ('a', 'a', '', '', '', b"Must provide Password"),
    ('a', 'a', 'a', '', '', b"Must provide Confirmation"),
    ('a', 'a', 'a', 'a', '', b"Must provide Role"),
    ('a', 'a', 'a', 'b', 'b', b"Passwords don&#39;t match"),
    ('test', 'test', 'test', 'test', 'test', b'Wrong role'),
    ('test', 'test', 'test', 'test', 'owner', b'Wrong role'),
    ('test', 'test', 'test', 'test', 'admin', b'Username/Email already exists in the company database'),
    ('a', 'a', 'a', 'a', 'admin', b'User added!'),
))
def test_add_user_admin(client, auth, username, email, password, confirmation, role, message, app):
    auth.login_admin()
    with client:
        response = client.get('/add-user')
        assert response.status_code == 200
        
        response = client.post(
            '/add-user', data={'username': username, 'email': email, 'password': password, 'confirmation': confirmation, 'role': role},
            follow_redirects=True,
        )
        assert message in response.data

        if message == b'User added!':
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM users WHERE username = 'a'",
                ).fetchone() is not None

@pytest.mark.parametrize(('username', 'message'), (
    ('Angel', b"Can&#39;t edit the owner"),
    ('b', b"No such user exists in the company"),
))
def test_edit_user_get_admin(client, username, message, auth):
    auth.login_admin()
    with client:
        response = client.get('/edit-user?user=' + username,
        )
        print(response.data)
        assert message in response.data

@pytest.mark.parametrize(('username', 'email', 'password', 'confirmation', 'role', 'user', 'message'), (
    ('', '', '', '', '', 4, b"Must provide Username"),
    ('a', '', '', '', '', 4, b"Must provide Email"),
    ('a', 'a', '', '', '', 4, b"Must provide Password"),
    ('a', 'a', 'a', '', '', 4, b"Must provide Confirmation"),
    ('a', 'a', 'a', 'a', '', 4, b"Must provide Role"),
    ('a', 'a', 'a', 'a', 'a', 6, b'Something went wrong with that request'),
    ('test', 'a', 'a', 'a', 'user', 4, b'Username/email already in company database'),
    ('a', 'a', 'test', 'test', 'user', 1, b'Can&#39;t change role of the owner'),
    ('a', 'a', 'test', 'test', 'test', 4, b'Wrong role'),
    ('a', 'a', 'test', 'rr', 'admin', 4, b'Password doesn&#39;t match confirmation'),
    ('a', 'a', 'a', 'a', 'admin', 4, b'Database Updated!'),
))
def test_edit_user_post_admin(client, auth, username, email, password, confirmation, role, message, user, app):
    auth.login_admin()
    with client:
        response = client.post('/edit-user',
            data={'username': username, 'email': email, 'password': password, 'confirmation': confirmation, 'role': role, 'u': user},
            follow_redirects=True,
        )
        print(response.data)
        
        assert message in response.data
        

        if message == b'Database Updated!':
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM users WHERE username = 'a'",
                ).fetchone() is not None
        else:
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM users WHERE username = 'a'",
                ).fetchone() is None