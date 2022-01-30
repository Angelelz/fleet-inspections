import pytest
from fleets.db import get_db
from fleets.dictionaries import c1

def test_inspection_get_user(client, auth):
    auth.login_user()
    with client:
        assert client.get('/inspection').status_code == 200
        assert client.get('/inspection?vehicle=1').status_code == 200
        assert client.get('/inspection?vehicle=232').status_code == 302

def test_inspection_get_admin(client, auth):
    auth.login_admin()
    with client:
        assert client.get('/inspection').status_code == 200
        assert client.get('/inspection?vehicle=1').status_code == 200
        assert client.get('/inspection?vehicle=232').status_code == 302

def test_inspection_get_owner(client, auth):
    auth.login_owner()
    with client:
        assert client.get('/inspection').status_code == 200
        assert client.get('/inspection?vehicle=1').status_code == 200
        assert client.get('/inspection?vehicle=232').status_code == 302


@pytest.mark.parametrize(('miles', 'maintenance', 'date', 'vehicle', 'setting', 'message'), (
    ('', '', '', '1', True, b"Must provide Miles"),
    ('1', '', '', '1', True, b"Must provide Maintenance"),
    ('1', 'a', '', '1', True, b"Must provide Date"),
    ('1', 'a', 'a', '', True, b"Something went wrong with that request"),
    ('1', 'a', 'a', '123', True, b"Something went wrong with that request"),
    ('1', 'a', 'a', '1', False, "leak_sign"),
    ('1', 'a', 'a', '1', False, "windshield_fluid"),
    ('1', 'a', 'a', '1', False, "Inspection added!"),
))
def test_inspection_post_admin(client, auth, miles, maintenance, date, vehicle, setting, message, app):
    auth.login_admin()
    data = {'miles': miles, 'maintenance': maintenance, 'date': date, 'vehicle': vehicle}

    if setting:
        with client:
            response = client.post(
                '/inspection', data=data,
                follow_redirects=True,
            )
            
            assert message in response.data

    else:
        for c in c1:
            alert = "Must provide value for: "
            data[c[1]]=None
            data[c[2]]=None
            if c[0] == message:
                data[c[0]]=None
                alert += c[3]
            else:
                data[c[0]]=1
                
        with client:
            response = client.post(
                '/inspection', data=data,
                follow_redirects=True,
            )
            print(response.data)
            if message == "Inspection added!":
                assert message.encode() in response.data
            else:
                assert alert.encode() in response.data


            if message == "Inspection added!":
                with app.app_context():
                    assert get_db().execute(
                        "SELECT * FROM inspections WHERE date = 'a'",
                    ).fetchone() is not None
            else:
                with app.app_context():
                    assert get_db().execute(
                        "SELECT * FROM inspections WHERE date = 'a'",
                    ).fetchone() is None


@pytest.mark.parametrize(('miles', 'maintenance', 'date', 'vehicle', 'setting', 'message'), (
    ('', '', '', '1', True, b"Must provide Miles"),
    ('1', '', '', '1', True, b"Must provide Maintenance"),
    ('1', 'a', '', '1', True, b"Must provide Date"),
    ('1', 'a', 'a', '', True, b"Something went wrong with that request"),
    ('1', 'a', 'a', '123', True, b"Something went wrong with that request"),
    ('1', 'a', 'a', '1', False, "leak_sign"),
    ('1', 'a', 'a', '1', False, "windshield_fluid"),
    ('1', 'a', 'a', '1', False, "Inspection added!"),
))
def test_inspection_post_user(client, auth, miles, maintenance, date, vehicle, setting, message, app):
    auth.login_user()
    data = {'miles': miles, 'maintenance': maintenance, 'date': date, 'vehicle': vehicle}

    if setting:
        with client:
            response = client.post(
                '/inspection', data=data,
                follow_redirects=True,
            )
            
            assert message in response.data

    else:
        for c in c1:
            alert = "Must provide value for: "
            data[c[1]]=None
            data[c[2]]=None
            if c[0] == message:
                data[c[0]]=None
                alert += c[3]
            else:
                data[c[0]]=1
                
        with client:
            response = client.post(
                '/inspection', data=data,
                follow_redirects=True,
            )
            print(response.data)
            if message == "Inspection added!":
                assert message.encode() in response.data
            else:
                assert alert.encode() in response.data


            if message == "Inspection added!":
                with app.app_context():
                    assert get_db().execute(
                        "SELECT * FROM inspections WHERE date = 'a'",
                    ).fetchone() is not None
            else:
                with app.app_context():
                    assert get_db().execute(
                        "SELECT * FROM inspections WHERE date = 'a'",
                    ).fetchone() is None