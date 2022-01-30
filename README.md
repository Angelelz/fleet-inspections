<p align="center">
    <img width="600" src="https://drive.google.com/uc?id=1K0psj5n-OoLHwowFkd0qegfuYNSB5XOV">
</p>

# Fleet inspections

## Video Demo:  <URL HERE>
## Description:
<img width="1100" src="https://drive.google.com/uc?id=1AxUYx21lKeD5LH0rLQsQws7OMgyqCPTH">

Fleets is a web project to allow companies to track their fleet inspections, issues and maintenance.
The company I currently work for does this the old way (paper inspections), making it a little tedious to track vehicle maintenance, issues or usage.
I wrote the app based on the project 9 

## Build/Run

#### Requirements

- Flask
- Flask-Session

```bash
$ pip install flask flask-session
```

#### Running the app:

To run the app from source, you need to install as a module by doing:
```bash
$ pip install -e .
```

On the project root folder.

Then execute:
```bash
$ export FLASK_APP="fleets"
$ flask run
```
Alternatively you can start the server using the app instace creator file myapp.py:
```bash
$ cd fleets
$ python3 myapp.py
```

#### Running on a wsgi server:

Install the the app as a module by following the instruccions above,
then on the server config file add the following lines:
```python
import sys
path = 'path/to/project/folder/fleets/'
if path not in sys.path:
    sys.path.append(path)

from myapp import app as application
```

## Testing

There are basic tests to run in the app if changes are made.
The tests cover logging in and out, register, adding/editing users, adding/editing/viewing vehicles, adding inspections and database operations.

#### Requirements

- pytest
- coverage
```bash
$ pip install pytest coverage
```

#### Running tests

Just execute the following in the project root folder:
```bash
$ pytest
```
```
================================== test session starts ==================================
platform linux -- Python 3.6.9, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /home/angel/repos/fleet-inspections, configfile: setup.cfg, testpaths: tests
collected 128 items                                                                     

tests/test_auth.py ..............                                                 [ 10%]
tests/test_db.py ..                                                               [ 12%]
tests/test_factory.py ..                                                          [ 14%]
tests/test_inspec.py ...................                                          [ 28%]
tests/test_pass.py .....................                                          [ 45%]
tests/test_users.py ..............................                                [ 68%]
tests/test_vehicles.py ........................................                   [100%]

================================= 128 passed in 26.29s ==================================
```

## Usage

The web app is live at [angelelz.pythonanywhere.com](https://angelelz.pythonanywhere.com/)

The company owner have to register an account with his company name, username, email and password.