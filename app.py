import datetime

import sqlite3
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, check_password, as_dict, permissions_required, check_inputs, best_fit
from large_tables import ins, c1
MAX_INSPECTIONS = 8

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["len"] = len

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_SAMESITE"] = 'Lax'
Session(app)

# Database Name
db_path = "./fleets.db"
db = sqlite3.connect(db_path)
db.execute('''CREATE TABLE IF NOT EXISTS companys
               (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
               show_name TEXT, owner TEXT NOT NULL)''')
db.execute('''CREATE TABLE IF NOT EXISTS users
               (u_id INTEGER PRIMARY KEY, c_id INTEGER NOT NULL,
               username TEXT NOT NULL, email TEXT NOT NULL,
               hash TEXT NOT NULL, role TEXT NOT NULL, FOREIGN KEY (c_id)
               REFERENCES companys (id) ON DELETE CASCADE ON UPDATE NO ACTION)''')
db.execute('''CREATE TABLE IF NOT EXISTS vehicles
               (v_id INTEGER PRIMARY KEY, c_id INTEGER NOT NULL,
               make TEXT NOT NULL, model TEXT NOT NULL,
               year TEXT NOT NULL, number TEXT NOT NULL, vin TEXT UNIQUE NOT NULL,
               tag TEXT, FOREIGN KEY (c_id) REFERENCES companys (id) ON DELETE CASCADE
               ON UPDATE NO ACTION)''')
db.execute(ins)
db.commit()
db.close()


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Handle requests to the root
@app.route("/")
def index():
    """Handle requests to index"""
    # If user si not logged in, show an index page with some text
    if not session.get("user_id"):
        return render_template("index.html")

    # Get the user information from the DB
    users = []
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    user = as_dict(db.execute("SELECT * FROM users WHERE u_id = ? AND c_id = ?", [session.get("user_id"), session.get("c_id")]).fetchall())

    # If the user is admin or owner give them the user list and the vehicle list, otherwise just give them just the vehicles
    if user[0]["role"] in ["owner", "admin"]:
        users = as_dict(db.execute("SELECT * FROM users WHERE c_id = ?", [user[0]["c_id"]]).fetchall())
    vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY (number + 0)", [session["c_id"]]).fetchall())
    db.close()

    # Render index.html with the values from DB
    return render_template("index.html", user=user, users=users, vehicles=vehicles)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    # If request is a GET just show register.html
    if request.method == "GET":
        return render_template("register.html")

    # If request is post, process the data
    else:
        # Check that all inputs have data, if not, render an apology
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("You have to input " + checks[1])

        # Set the form data to variables
        name = request.form.get("username")
        email = request.form.get("email")
        company = request.form.get("company")

        # Get all the companies from DB
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        companys = as_dict(db.execute("SELECT * FROM companys WHERE name = ?", [company]).fetchall())
        db.close()

        # If company name exists return apology
        if len(companys) > 0:
            return apology("Company name already exists")

        # If password doesn't meet requierements return apology
        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        # If password and confirmation don't match return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # Insert company and user into database with current user as owner
        hashed_password = generate_password_hash(request.form.get("password"))
        db = sqlite3.connect(db_path)
        try:
            with db:
                cid = db.execute("INSERT INTO companys (name, owner) VALUES(?, ?)", (company, name)).lastrowid
                db.execute("INSERT INTO users (c_id, username, email, hash, role) VALUES(?, ?, ?, ?, ?)",
                            (cid, name, email, hashed_password, "owner"))
        except:
            # If there was an error flash the user
            db.close()
            flash('Error registering Company/User, contact support', 'error')
            return render_template("login.html")
        else:
            # Flask confirmation and redirect to login page
            db.close()
            flash('Company/User registered')
            return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check that all inputs have data, if not, render an apology
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1], 403)

        # Get company from database
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        company = as_dict(db.execute("SELECT * FROM companys WHERE name = ?", [request.form.get("company")]).fetchall())

        # If company is not in db render an apology
        if len(company) != 1:
            db.close()
            return apology("Company not found", 403)

        # Get user from DB
        rows = as_dict(db.execute("SELECT * FROM users WHERE username = ? AND c_id = ?", [request.form.get("username"), company[0]["id"]]).fetchall())
        db.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in along with company and role
        session["user_id"] = rows[0]["u_id"]
        session["c_id"] = rows[0]["c_id"]
        session["role"] = rows[0]["role"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user home
    flash('You logged out')
    return redirect("/")

@app.route("/add-vehicle", methods=["GET", "POST"])
@login_required
def add_vehicle():
    """Adds a new vehicle to the company"""
    # If request is GET render the page
    if request.method == "GET":
        return render_template("add-vehicle.html")

    # If request is post:
    else:
        # Check that all inputs have data (except tag), if not, render an apology
        checks = check_inputs(request.form, ["tag"])
        if checks[0]:
            return apology("must provide " + checks[1])

        # Check if year is a 4digit number, if not, render an apology
        try:
            if int(request.form.get("year")) < 1900:
                return apology("Year must have 4 digits")
        except:
            return apology("Year must be a 4 digits number")

        # Create an array with the form data
        vehicle = [ session.get("c_id"),
                    request.form.get("make"),
                    request.form.get("model"),
                    request.form.get("year"),
                    request.form.get("number"),
                    request.form.get("vin"),
                    request.form.get("tag")]

        # Ensure Vehicle id is unique
        db = sqlite3.connect(db_path)
        v = db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?", [request.form.get("number"), session.get("c_id")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("A vehicle with that ID already exists in the company database")

        # Ensure VIN is unique
        v = db.execute("SELECT * FROM vehicles WHERE vin = ?", [request.form.get("vin")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("A vehicle with that VIN already exists in the company database")

        # Insert Vehicle into database
        try:
            with db:
                db.execute("INSERT INTO vehicles (c_id, make, model, year, number, vin, tag) VALUES(?, ?, ?, ?, ?, ?, ?)", vehicle)
        except:
            # If there was an error flash the user
            db.close()
            flash('Database: Error adding vehicle, contact support', 'error')
            return redirect("/")
        else:
            # Redirect to home
            db.close()
            flash('Vehicle added!')
            return redirect("/")

@app.route("/add-user", methods=["GET", "POST"])
@login_required
@permissions_required
def add_user():
    """Adds a new user to the company"""
    # If request is GET render the page
    if request.method == "GET":
        return render_template("add-user.html")

    # If request is post:
    else:
        # Check that all inputs have data, if not, render an apology
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        # If password doesn't meet requierements return apology
        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        # If password and confirmation don't match return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        # If role is not admin or user render an apology (Can only have 1 owner)
        if request.form.get("role") not in ["admin", "user"]:
            return apology("Wrong role")

        # Set the data into an array
        user = [ session.get("c_id"),
                    request.form.get("username"),
                    request.form.get("email"),
                    generate_password_hash(request.form.get("password")),
                    request.form.get("role")]

        # Query DB for the same username or email in the company, if exists return an apology
        db = sqlite3.connect(db_path)
        v = db.execute("SELECT * FROM users WHERE (username = ? OR email = ?) AND c_id = ?",
                         [request.form.get("username"), request.form.get("email"), session.get("c_id")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("Username/Email already exists in the company database")

        # Insert user into DB
        try:
            with db:
                db.execute("INSERT INTO users (c_id, username, email, hash, role) VALUES(?, ?, ?, ?, ?)", user)
        except:
            # If there was an error flash the user
            db.close()
            flash('Database: Error adding user, contact support', 'error')
            return redirect("/")
        else:
            # Redirect to home
            db.close()
            flash('User added')
            return redirect("/")



@app.route("/inspection", methods=["GET", "POST"])
@login_required
def inspection():
    """Creates an inspection"""
    # If request is GET render the page
    if request.method == "GET":
        # If vehicle is not in get request
        if not request.args.get("vehicle"):
            # Get all the company vehicles from DB
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number", [session.get("c_id")]).fetchall())
            db.close()

            # If only one vehicle just go to inspect that one, otherwise render template to select it
            if len(vehicles) == 1:
                return redirect("/inspection?vehicle=" + str(vehicles[0]["number"]))
            else:
                return render_template("inspection.html", vehicles=vehicles)

        # If vechicle is in get request
        else:
            # Query DB for that vehicle
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            v = as_dict(db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?",
                                    [request.args.get("vehicle"), session.get("c_id")]).fetchall())

            # If no such vehicle redirect to inspection
            if len(v) != 1:
                db.close()
                return redirect("/inspection")

            # Get next oil change from last inspection
            oil = db.execute("SELECT next_oil FROM inspections WHERE v_id = ? ORDER BY date DESC", [v[0]["v_id"]]).fetchone()
            db.close()

            # pass the info to render the inspection for that vehicle
            return render_template("inspection.html", inspection=c1, vehicle=request.args.get("vehicle"),
                                        v=v[0], oil=oil, date=datetime.date.today().strftime('%Y-%m-%d'))

    # If request is post (Meaning: user sumbited an inspection)
    else:
        # Check that the important inputs have data, if not, render an apology
        checks = check_inputs(request.form, ["v", "miles", "maintenance", "date"], False)
        if checks[0]:
            return apology("must provide " + checks[1])

        # Create the DB query dinamically depending on the data sumbited
        # query will always start the same way
        query = "INSERT INTO inspections (c_id, u_id, v_id, miles, next_oil, date"

        # values will be all the question marks (which should be the same number as variables to insert)
        values = "(?, ?, ?, ?, ?, ?"

        # vars will be an array with al the variables to insert
        vars = [session.get("c_id"), session.get("user_id"),
                request.form.get("v"), request.form.get("miles"),
                request.form.get("maintenance"), request.form.get("date")]

        # iterate over c1 to get whatever the user submited
        for c in c1:
            if request.form.get(c[0]):
                query += ", " + c[0]
                values += ", ?"
                vars.append(request.form.get(c[0]))
            if request.form.get(c[1]):
                query += ", " + c[1]
                values += ", ?"
                vars.append(request.form.get(c[1]))
            if request.form.get(c[2]):
                query += ", " + c[2]
                values += ", ?"
                vars.append(request.form.get(c[2]))

        # assemble the final query string
        query += ") VALUES " + values + ")"

        # Submit the quiery to the database
        db = sqlite3.connect(db_path)
        try:
            with db:
                db.execute(query, vars)
        except:
            # If there was an error flash the user
            db.close()
            flash('Database: Error adding inspection, contact support', 'error')
            return redirect("/")
        else:
            # Confirm to the user and redirect to home
            db.close()
            flash('Inspection loaded into database!')
            return redirect("/")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change Password"""
    # If request is GET render the page
    if request.method == "GET":
        return render_template("password.html")

    # If request is post (Meaning: user sumbited a password change)
    else:
        # query DB for user
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        user = as_dict(db.execute("SELECT * FROM users WHERE u_id = ?", [session.get("user_id")]).fetchall())
        db.close()

        # Check that all inputs have data, if not, render an apology
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        # If password doesn't meet requierements return apology
        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        # Ensure username exists and password is correct
        if len(user) != 1 or not check_password_hash(user[0]["hash"], request.form.get("old-password")):
            return apology("Wrong password")

        # If password and confirmation don't match return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confimation don't match")

        # Update database with new password
        hashed_password = generate_password_hash(request.form.get("password"))
        db = sqlite3.connect(db_path)
        try:
            with db:
                db.execute("UPDATE users SET hash = ? WHERE u_id = ?", [hashed_password, session.get("user_id")])
        except:
            # If there was an error flash the user
            db.close()
            flash('Error changing password, contact support', 'error')
            return redirect("/")
        else:
            # Flask confirmation and redirect to home
            db.close()
            flash('Password changed!')
            return redirect("/")


@app.route("/edit-vehicle", methods=["GET", "POST"])
@login_required
def edit_vehicle():
    """Edit a Vehicle already in the database"""
    # If request is GET render the page
    if request.method == "GET":
        # If vehicle is not in get request
        if not request.args.get("vehicle"):
            # Get all the company vehicles from DB
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY (number + 0)", [session.get("c_id")]).fetchall())
            db.close()
            # If only one vehicle just go to edit that one, otherwise render template to select it
            if len(vehicles) == 1:
                return redirect("edit-vehicle?vehicle=" + str(vehicles[0]["number"]))
            else:
                return render_template("edit-vehicle.html", vehicles=vehicles)

        # If vechicle is in get request
        else:
            # Query DB for that vehicle
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            v = as_dict(db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?",
                                    [request.args.get("vehicle"), session.get("c_id")]).fetchall())
            db.close()

            # If no such vehicle redirect to edit-vehicle otherwise pass the info to render the edit template for that vehicle
            if len(v) == 0:
                return redirect("/edit-vehicle")
            else:
                return render_template("edit-vehicle.html", vehicle=request.args.get("vehicle"), v=v[0])

    # If request is post (Meaning: user sumbited an edit)
    else:
        # Check that all the inputs have data except for tag, if not, render an apology
        checks = check_inputs(request.form, ["tag"])
        if checks[0]:
            return apology("must provide " + checks[1])

        # Check if year is a 4digit number, if not, render an apology
        try:
            if int(request.form.get("year")) < 1900:
                return apology("Year must have 4 digits")
        except:
            return apology("Year must be a 4 digits number")

        # Create an array with the form data
        vehicle = [ request.form.get("make"),
                    request.form.get("model"),
                    request.form.get("year"),
                    request.form.get("number"),
                    request.form.get("tag") ]

        # Get the vehicle from database
        db = sqlite3.connect(db_path)
        v_id = db.execute("SELECT v_id FROM vehicles WHERE number = ? AND c_id = ?",
                            [request.form.get("v"), session.get("c_id")]).fetchone()

        # If no vehicle, return an apology
        if len(v_id) != 1:
            db.close()
            return apology("something went wrong with that request")

        # Add vehicle id to the vehicle array and update the vehicle with the new data
        vehicle.append(v_id[0])
        try:
            with db:
                db.execute("UPDATE vehicles SET make = ?, model = ?, year = ?, number = ?, tag = ? WHERE v_id = ?", vehicle)
        except:
            # If the was an error flash the user
            db.close()
            flash('Error editing vehicle, contact support', 'error')
            return redirect("/")
        else:
            # Flash the user the confimation and redirect to home
            db.close()
            flash('Database Updated!')
            return redirect("/")


@app.route("/edit-user", methods=["GET", "POST"])
@permissions_required
@login_required
def edit_user():
    """Edit a user already in the database"""
    # If request is GET render the page
    if request.method == "GET":
        # If user is not in get request
        if not request.args.get("user"):
            # Get all the company users from DB except for the owner
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            users = as_dict(db.execute('''SELECT * FROM users WHERE c_id = ? AND role != "owner"''', [session.get("c_id")]).fetchall())
            db.close()
            # If only one user just go to edit that one, otherwise render template to select it
            if len(users) == 1:
                return redirect("/edit-user?user=" + str(users[0]["username"]))
            else:
                return render_template("edit-user.html", users=users)

        # If vechicle is in get request
        else:
            # Query DB for that user and the company
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            u = as_dict(db.execute("SELECT * FROM users WHERE username = ?", [request.args.get("user")]).fetchall())
            c = as_dict(db.execute("SELECT * FROM companys WHERE id = ?", [session.get("c_id")]).fetchall())
            db.close()

            # If trying to edit owner return an apology
            if c[0]["owner"] == request.args.get("user"):
                return apology("Can't edit the owner")

            # If no such user redirect to edit-user otherwise pass the info to render the edit template for that user
            if len(u) != 1:
                return redirect("/edit-user")
            else:
                return render_template("edit-user.html", user=request.args.get("user"), u=u[0])

    # If request is post (Meaning: user sumbited an edit)
    else:
        # Check that all the inputs have data except for tag, if not, render an apology
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        # Get the user and all other users from the DB
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        u = as_dict(db.execute("SELECT * FROM users WHERE u_id = ?", [request.form.get("u")]).fetchall())
        others = as_dict(db.execute("SELECT * FROM users WHERE u_id != ? AND c_id = ?",
                            [request.form.get("u"), session.get("c_id")]).fetchall())
        db.close()

        # If user is not in DB return an apology
        if len(u) != 1:
            return apology("something went wrong with that request")

        # If trying to submit a user/email that already exists return an apology
        for other in others:
            if u[0]["username"] == other["username"] or u[0]["email"] == other["email"]:
                return apology("username/email already in company database")

        # If trying to edit the role of the owner return an apology
        if u[0]["role"] == "owner" and request.form.get("role") != "owner":
            return apology("can't change role of the owner")

        # If trying to sumbit a role not supported return an apology
        if request.form.get("role") not in ["admin", "user"]:
            return apology("wrong role")

        # If password doesn't meet requierements return apology
        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        # If password and confirmation don't match return apology
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation don't match")

        # Set the data into an array
        user = [ request.form.get("username"),
                    request.form.get("email"),
                    generate_password_hash(request.form.get("password")),
                    request.form.get("role"),
                    request.form.get("u")]

        # Insert user into DB
        db = sqlite3.connect(db_path)
        try:
            with db:
                db.execute("UPDATE users SET username = ?, email = ?, hash = ?, role = ? WHERE u_id = ?", user)
        except:
            # If there was an error flash the user
            db.close()
            flash('Error editing user, contact support', 'error')
            return redirect("/")
        else:
            # Redirect to home
            db.close()
            flash('Database Updated!')
            return redirect("/")


@app.route("/vehicles", methods=["GET", "POST"])
@permissions_required
@login_required
def vehicles():
    """View Vehicles"""

    def get_inspections(request_arg):
        """Get inspections from database"""
        # Get the vehicle from DB
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        vehicle = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? AND number = ?",
                                [session.get("c_id"), request_arg.get("vehicle")]).fetchall())

        # If vehicle submited not in database redirect to vehicles
        if len(vehicle) != 1:
            db.close()
            return redirect("/vehicles")

        # Get all the vehicles from DB
        v = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY (number + 0)",
                                [session.get("c_id")]).fetchall())

        # Get MAX_INSPECTIONS fron the vehicle sumbited and the users from DB
        inspections = as_dict(db.execute('''SELECT * FROM inspections, users WHERE inspections.c_id = ? AND inspections.v_id = ?
                                            AND inspections.u_id = users.u_id ORDER BY inspections.date DESC LIMIT ?''',
                                            [session.get("c_id"), vehicle[0]["v_id"], MAX_INSPECTIONS]).fetchall())
        db.close()

        # Create an array called inspection with this structure:
        # [Issue description, Issue name, Date, User (that made the inspection)] for every issue and inspection
        inspection = []

        # itearete over every inspection
        for i in inspections:
            found_issue = False

            #iterate over every issue description
            for c in c1:
                # If the inspection has this issue flagged append a new array
                if i[c[0]] == 0:
                    found_issue = True
                    inspection.append([i[c[1]], c[3], i["date"], i["username"]])

            # If there was no issue in the inspection we still want to show inspection data with no issue
            if not found_issue:
                inspection.append(["No issue", "No issue", i["date"], i["username"]])

        # If no inspections just create an array with no data to show in page
        if len(inspection) < 1:
            inspection = [["No data", "No data", "No data", "No data"]]

        # If request is get just pass the data to render the template, otherwise jsonify data for javascript
        if request.method == "GET":
            return render_template("vehicles.html", vehicle=request.args.get("vehicle"), inspection=inspection, vehicles=v)
        else:
            return jsonify(inspection)

    # If request is GET render the page
    if request.method == "GET":
        # If vehicle is not in get request
        if not request.args.get("vehicle"):
            # Get all the company vehicles and inspections from DB
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY (number + 0)", [session.get("c_id")]).fetchall())
            inspections = as_dict(db.execute("SELECT * FROM inspections WHERE c_id = ? ORDER BY date DESC", [session.get("c_id")]).fetchall())
            db.close()

            # Fancy way of creating a dictionary with the vehicles as keys and a list of inspections as values
            v = {ve["number"]:[[i["next_oil"], i["miles"], i["date"]] for i in inspections if i["v_id"] == ve["v_id"]] for ve in vehicles}

            # Append a projection of the date of the next oil change
            for vehicle, i in v.items():
                # If there are no inspections just append no data array
                if len(i) < 1:
                    i.append(["No data", "No data", "No data", "No data"])
                # If there is more than 2, we can proceed with the calculation
                elif len(i) > 2:
                    # Variable that we need for the best_fit function
                    miles_oil = 0
                    miles = []
                    dates = []
                    j = 0
                    # Need to convert dates to numbers to calculate best fit. Milliseconds from 01/01/1970 seem appropiate
                    d2 = datetime.datetime.strptime("1970-01-01", '%Y-%m-%d')
                    for array in i:
                        if j > MAX_INSPECTIONS:
                            break
                        # Get latest mileage to oil change
                        miles_oil = max(miles_oil, array[0])
                        # Append the mileage to the miles array
                        miles.append(array[1])
                        # Append the date in milliseconds from 1970 to the dates array
                        d1 = datetime.datetime.strptime(array[2], '%Y-%m-%d')
                        dates.append((d1 - d2)/datetime.timedelta(milliseconds=1))
                        j += 1
                    # Calculate projection
                    next_oil = d2 + datetime.timedelta(milliseconds=best_fit(dates, miles, miles_oil))
                    # Append calculation in date format
                    i[0].append(next_oil.strftime('%Y-%m-%d'))
                else:
                    i[0].append("Need more data")

            # Render template passing the data
            return render_template("vehicles.html", vehicles=v)

        # If vehicle is in get request, let the get_inspections function handle it
        else:
            return get_inspections(request.args)

    # If the request is post with the value of vehicle let the function handle the javascript request
    elif request.form:
        return get_inspections(request.form)

    # If the request is post without the value of vehicle
    else:

        # Get all the vehicles and inspections of the company
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        inspections = as_dict(db.execute("SELECT v_id, date, miles, next_oil FROM inspections WHERE c_id = ? ORDER BY date DESC", [session.get("c_id")]).fetchall())
        vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number", [session.get("c_id")]).fetchall())
        db.close()

        # Create the data for the graphs for all vehicles including projections
        graph_data = []
        # Iterate over every vehicle
        for v in vehicles:
            # Dictionary of dates and miles for the vehicle
            d = {v["number"]:{"dates":[],"miles":[]}}
            miles_oil = 0
            j = 0
            # Iterate over every inspection
            for i in inspections:
                # If current inspection corresponds to the current vehicle append date and miles of this inspection
                if i["v_id"] == v["v_id"]:
                    if j > MAX_INSPECTIONS:
                        break
                    d1 = datetime.datetime.strptime(i["date"], '%Y-%m-%d')
                    d2 = datetime.datetime.strptime("1970-01-01", '%Y-%m-%d')
                    d[v["number"]]["dates"].append((d1 - d2)/datetime.timedelta(milliseconds=1))
                    d[v["number"]]["miles"].append(i["miles"])
                    miles_oil = max(i["next_oil"], miles_oil)
                    j += 1
            d[v["number"]]["dates"].reverse()
            d[v["number"]]["miles"].reverse()
            # Calculate projections with al the inspections
            next_oil = best_fit(d[v["number"]]["dates"], d[v["number"]]["miles"], miles_oil)
            if next_oil != 0:
                d[v["number"]]["dates"].append(next_oil)
                d[v["number"]]["miles"].append(miles_oil)
            graph_data.append(d)

        return jsonify(graph_data)