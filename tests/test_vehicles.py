import pytest
from fleets.db import get_db

def test_vehicles_user(client, auth):
    auth.login_user()
    with client:
        assert client.get('/add-vehicle').status_code == 200
        assert client.get('/edit-vehicle').status_code == 200
        assert client.get('/vehicles').status_code == 302
        assert client.get('/vehicles?vehicle=1').status_code == 302
        assert client.get('/vehicles?vehicle=232').status_code == 302

def test_vehicles_admin(client, auth):
    auth.login_admin()
    with client:
        assert client.get('/add-vehicle').status_code == 200
        assert client.get('/edit-vehicle').status_code == 200
        assert client.get('/vehicles').status_code == 200
        assert client.get('/vehicles?vehicle=1').status_code == 200
        assert client.get('/vehicles?vehicle=232').status_code == 302

def test_vehicles_owner(client, auth):
    auth.login_owner()
    with client:
        assert client.get('/add-vehicle').status_code == 200
        assert client.get('/edit-vehicle').status_code == 200
        assert client.get('/vehicles').status_code == 200

def test_add_vehicle_user(client, auth):
    auth.login_user()
    with client:        
        response = client.post(
            '/add-vehicle', data={'year': '2000', 'make': 'a', 'model': 'a', 'number': 'a', 'tag': 'a', 'vin': 'a'},
        )
        print(response)
        
        assert response.status_code == 302

@pytest.mark.parametrize(('year', 'make', 'model', 'number', 'tag', 'vin', 'message'), (
    ('', '', '', '', '', '', b"Must provide Year"),
    ('a', '', '', '', '', '', b"Must provide Make"),
    ('a', 'a', '', '', '', '', b"Must provide Model"),
    ('a', 'a', 'a', '', '', '', b"Must provide Number"),
    ('a', 'a', 'a', 'a', '', '', b"Must provide Vin"),
    (15, 'a', 'a', 'a', '', 'b', b"Year must have 4 digits"),
    ('15', 'a', 'a', 'a', '', 'b', b"Year must have 4 digits"),
    ('asd', 'a', 'a', 'a', '', 'b', b"Year must be a 4 digits number"),
    ('1999', 'a', 'a', 8, '', 'b', b"A vehicle with that ID already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'whatever', b"A vehicle with that VIN already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'vinnumber1', b"Vehicle added!"),
))
def test_add_vehicle_admin(client, auth, year, make, model, number, tag, vin, message, app):
    auth.login_admin()
    with client:
        response = client.get('/add-vehicle')
        assert response.status_code == 200
        
        response = client.post(
            '/add-vehicle', data={'year': year, 'make': make, 'model': model, 'number': number, 'tag': tag, 'vin': vin},
            follow_redirects=True,
        )
        assert message in response.data

        if message == b'Vehicle added!':
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM vehicles WHERE number = 'a'",
                ).fetchone() is not None
        else:
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM vehicles WHERE number = 'a'",
                ).fetchone() is None

@pytest.mark.parametrize(('year', 'make', 'model', 'number', 'tag', 'vin', 'message'), (
    ('', '', '', '', '', '', b"Must provide Year"),
    ('a', '', '', '', '', '', b"Must provide Make"),
    ('a', 'a', '', '', '', '', b"Must provide Model"),
    ('a', 'a', 'a', '', '', '', b"Must provide Number"),
    ('a', 'a', 'a', 'a', '', '', b"Must provide Vin"),
    (15, 'a', 'a', 'a', '', 'b', b"Year must have 4 digits"),
    ('15', 'a', 'a', 'a', '', 'b', b"Year must have 4 digits"),
    ('asd', 'a', 'a', 'a', '', 'b', b"Year must be a 4 digits number"),
    ('1999', 'a', 'a', 8, '', 'b', b"A vehicle with that ID already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'whatever', b"A vehicle with that VIN already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'vinnumber1', b"Vehicle added!"),
))
def test_add_vehicle_user(client, auth, year, make, model, number, tag, vin, message, app):
    auth.login_user()
    with client:
        response = client.get('/add-vehicle')
        assert response.status_code == 200
        
        response = client.post(
            '/add-vehicle', data={'year': year, 'make': make, 'model': model, 'number': number, 'tag': tag, 'vin': vin},
            follow_redirects=True,
        )
        assert message in response.data

        if message == b'Vehicle added!':
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM vehicles WHERE number = 'a'",
                ).fetchone() is not None
        else:
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM vehicles WHERE number = 'a'",
                ).fetchone() is None

@pytest.mark.parametrize(('vehicle'), (
    ('2'),
    ('49'),
))
def test_edit_vehicle_get_admin(client, vehicle, auth):
    auth.login_admin()
    with client:
        response = client.get('/edit-vehicle?vehicle=' + vehicle,
        )
        print(response.data)
        if vehicle == '2':
            assert response.status_code == 200
        else:
            assert response.status_code == 302

@pytest.mark.parametrize(('year', 'make', 'model', 'number', 'tag', 'vin', 'vehicle', 'message'), (
    ('', '', '', '', '', '', '', b"Must provide Year"),
    ('a', '', '', '', '', '', '', b"Must provide Make"),
    ('a', 'a', '', '', '', '', '', b"Must provide Model"),
    ('a', 'a', 'a', '', '', '', '', b"Must provide Number"),
    ('a', 'a', 'a', 'a', '', '', '', b"Must provide Vin"),
    ('1999', 'a', 'a', 'a', '', 'b', '', b"Must provide Vehicle"),
    (15, 'a', 'a', 'a', '', 'b', 'b', b"Year must have 4 digits"),
    ('15', 'a', 'a', 'a', '', 'b', 'b', b"Year must have 4 digits"),
    ('asd', 'a', 'a', 'a', '', 'b', 'b', b"Year must be a 4 digits number"),
    ('1999', 'a', 'a', 8, '', 'b', '1', b"A vehicle with that ID already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'whatever', '1', b"A vehicle with that VIN already exists in the company database"),
    ('1999', 'a', 'a', 'a', '', 'whatever', '49', b"Something went wrong with that request"),
    ('1999', 'a', 'a', 'a', '', 'vinnumber1', '1', b"Database Updated!"),
))
def test_edit_vehicle_post_admin(client, auth, year, make, model, number, tag, vin, vehicle, message, app):
    auth.login_admin()
    with client:
        response = client.post('/edit-vehicle',
            data={'year': year, 'make': make, 'model': model, 'number': number, 'tag': tag, 'vin': vin, 'vehicle': vehicle},
            follow_redirects=True,
        )
        print(response.data)
        
        assert message in response.data
        

        if message == b'Database Updated!':
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM vehicles WHERE number = ?", [number]
                ).fetchone() is not None
        else:
            with app.app_context():
                assert get_db().execute(
                    "SELECT * FROM users WHERE username = 'a'",
                ).fetchone() is None