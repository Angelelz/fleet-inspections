<p align="center">
    <img width="600" src="https://drive.google.com/uc?id=1K0psj5n-OoLHwowFkd0qegfuYNSB5XOV">
</p>

# Fleet inspections

## Video Demo:  [FLEETS (Youtube)](https://youtu.be/ZHPEpYX1vEY)
## Description:
<p align="center">
<img width="800" src="https://drive.google.com/uc?id=1AxUYx21lKeD5LH0rLQsQws7OMgyqCPTH">
</p>

Fleets is a web project to allow companies to track their fleet inspections, issues and maintenance.
The company I currently work for does this the old way (paper inspections), making it a little tedious to track vehicle maintenance, issues or usage.
I wrote the app based on the cs50 project from week 9 "finance" using flask.

## Build/Run

#### Requirements

- Flask
- Flask-Session

```bash
$ pip install flask flask-session
```

#### Running the app:

To run the app from source, you need to install it as a module by doing:
```bash
$ pip install -e .
```

On the project root folder.

Then execute:
```bash
$ export FLASK_APP="fleets"
$ flask run
```
Alternatively, you can start the server using the app instance creator file myapp.py:
```bash
$ cd fleets
$ python3 myapp.py
```

#### Running on a wsgi server:

Install the app as a module by following the instructions above, then on the server config file add the following lines:
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

#### Register
The web app is live for now at [angelelz.pythonanywhere.com](https://angelelz.pythonanywhere.com/)

The company owner has to register an account with his company name, his username, email and password.
There is client-side protection on every input field, but if those aren't effective there is also protection on the server.

<p align="center">
<img width="800" src="https://drive.google.com/uc?id=1Axom-A8HbpH_8L8BdGtbafYMlhiS5PA2">
</p>

The feedback is shown as an error alert using the flash feature from flask. And as soon as the server detects an error, it renders the same page with the alert, keeping everything the user has written in the input fields.

#### Logging in
After signing up, the owner can log in using his/her new credentials.
The index page will show the users and vehicles in the company.
The user and vehicle tables dynamically hide/show columns based on the viewport width to adapt to mobile use. I used random vin data for the purpose of this demonstration.
<p align="center">
<img width=800" src="https://drive.google.com/uc?id=1AyaTfE0i5thiQgMlmUtSKJoTiz5CEAmW">
<img width="300" src="https://drive.google.com/uc?id=1B50uVBAE3N-5hUNvQxL84cBBr9j-rbYF">
</p>

#### Adding/editing users
Once logged in, the owner can add users and/or vehicles to start tracking them, or let employees track them.
There are 3 user roles implemented in this project:

- Owner: Which can only be 1 for the company, and is set up during registration.
- Admin: Who has all permissions the owner has.
- User: Who does not have permissions to add/edit users, or see vehicles tracking and inspection data.

The index view for an user with `user` role:
<img width="800" src="https://drive.google.com/uc?id=1B9EtWtatD1rJqMm8EI9_gYzddqzzwBtQ">

The owner/admin can add/edit users by clicking in the `Users` dropdown menu and then clicking the corresponding link.

<img width="800" src="https://drive.google.com/uc?id=1B8wOZLp95-LEEcyCbTUS2SXAVz4eCNvM">

Of course, an user with `user` role, will not have access to this features, for him/her the nav bar will look different, and any attempt to access protected pages will give him a flash and a redirect to index.

### Adding/editing vehicles
Users can add/edit vehicles by clicking the corresponding link in the nav bar.
All the fields are required except for the tag.

The user can input the vehicle data manually or click on the `Start/Stop the scanner` button to scan the VIN barcode using the camera on his/her phone.

<img width="800" src="https://drive.google.com/uc?id=1B9PDAiv6ECfRWE-OVz1X3vXXc2ZxbAuK">


This feature was possible thanks to the [QuaggaJS library](https://serratus.github.io/quaggaJS/) for Javascript, which was used to decode the VIN from the barcode, and the [Vehicle API](https://vpic.nhtsa.dot.gov/api/) provided by the NHTSA, which was used to decode the VIN and extract the vehicle information from it.

### Inspecting a vehicle
For now, there is only one template for vehicle inspections, based on my company's inspection sheet.
All the fields are required. Whenever there is an item not ok, an input field shows up to allow for some notes to be written.

<img width="800" src="https://drive.google.com/uc?id=1BNlB7IBVRuwWFvKbHpC5hUTyqMqQwkEy">

### Viewing vehicle issues and maintenance projections
##### Viewing all vehicles
This is the important functionality of the project.
When an owner/admin clicks on the `View vehicles` button, he/she gets a table listing all the vehicles with the latest inspection date, mileage and projected date of the next oil change (based on the regular inspections mileage data).
The table will show in red any vehicle with mileage bigger that the next oil change mileage, meaning the vehicle needs to go for maintenance.

<img width="600" src="https://drive.google.com/uc?id=1BOwxyDwcQN2XfLjE1IxLarTmC5SCP78y">

At the bottom, a graph shows up with the dates and mileages of the last 8 inspections for each vehicle. Each vehicle also shows up with the last point being the oil change projection date. On hovering over any point, the data for that point will be shown.
This graph was made possible using the [Chart.js plugin](https://www.chartjs.org/).

##### Viewing one particular vehicle
By clicking on any vehicle row, the detail view for that vehicle is open. A table with the latest 8 inspections is shown with all the issues on those inspections.

<img width="600" src="https://drive.google.com/uc?id=1BWUH0fKSbhsoaMy6Xj8vOsoF1wgEBS8k">

The graph is also updated to show only that vehicle.