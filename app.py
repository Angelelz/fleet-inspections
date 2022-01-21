import dbm
import os
import datetime

import sqlite3
from flask import Flask, jsonify, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd, check_password, as_dict, permissions_required, check_inputs
from large_tables import ins, c1

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["len"] = len

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
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
    """Show portfolio of stocks"""
    if session.get("user_id") == None or not session["user_id"]:
        return render_template("index.html")

    users = []
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    user = as_dict(db.execute("SELECT * FROM users WHERE u_id = ? AND c_id = ?", [session["user_id"], session["c_id"]]).fetchall())

    if user[0]["role"] in ["owner", "admin"]:
        users = as_dict(db.execute("SELECT * FROM users WHERE c_id = ?", [user[0]["c_id"]]).fetchall())
    vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ?", [session["c_id"]]).fetchall())
    db.close()
    return render_template("index.html", user=user, users=users, vehicles=vehicles)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("You have to input " + checks[1])

        name = request.form.get("username")
        email = request.form.get("email")
        company = request.form.get("company")

        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        companys = as_dict(db.execute("SELECT * FROM companys WHERE name = ?", [company]).fetchall())
        db.close()

        if len(companys) > 0:
            return apology("Company name already exists")

        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        hashed_password = generate_password_hash(request.form.get("password"))
        db = sqlite3.connect(db_path)
        cid = db.execute("INSERT INTO companys (name, owner) VALUES(?, ?)", (company, name)).lastrowid
        db.execute("INSERT INTO users (c_id, username, email, hash, role) VALUES(?, ?, ?, ?, ?)",
                    (cid, name, email, hashed_password, "owner"))
        db.commit()
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

        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1], 403)

        # Query database for username
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        company = as_dict(db.execute("SELECT * FROM companys WHERE name = ?", [request.form.get("company")]).fetchall())

        if len(company) != 1:
            db.close()
            return apology("Company not found", 403)

        rows = as_dict(db.execute("SELECT * FROM users WHERE username = ? AND c_id = ?", [request.form.get("username"), company[0]["id"]]).fetchall())
        db.close()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
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

    # Redirect user to login form
    flash('You logged out')
    return redirect("/")

@app.route("/add-vehicle", methods=["GET", "POST"])
@login_required
def add_vehicle():
    """Adds a new vehicle to the company"""
    if request.method == "GET":
        return render_template("add-vehicle.html")

    else:
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        try:
            if int(request.form.get("year")) < 1900:
                return apology("Year must have 4 digits")

        except:
            return apology("Year must be a 4 digits number")

        vehicle = [ session.get("c_id"),
                    request.form.get("make"),
                    request.form.get("model"),
                    request.form.get("year"),
                    request.form.get("number"),
                    request.form.get("vin"),
                    request.form.get("tag")]

        db = sqlite3.connect(db_path)
        v = db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?", [request.form.get("number"), session.get("c_id")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("A vehicle with that ID already exists in the company database")

        v = db.execute("SELECT * FROM vehicles WHERE vin = ?", [request.form.get("vin")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("A vehicle with that VIN already exists in the company database")

        db.execute("INSERT INTO vehicles (c_id, make, model, year, number, vin, tag) VALUES(?, ?, ?, ?, ?, ?, ?)", vehicle)
        db.commit()
        db.close()
        flash('Vehicle added!')
        return redirect("/")

@app.route("/add-user", methods=["GET", "POST"])
@login_required
@permissions_required
def add_user():
    """Adds a new user to the company"""
    if request.method == "GET":
        return render_template("add-user.html")

    else:
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        if request.form.get("role") not in ["admin", "user"]:
            return apology("Wrong role")

        user = [ session.get("c_id"),
                    request.form.get("username"),
                    request.form.get("email"),
                    generate_password_hash(request.form.get("password")),
                    request.form.get("role")]

        db = sqlite3.connect(db_path)
        v = db.execute("SELECT * FROM users WHERE (username = ? OR email = ?) AND c_id = ?",
                         [request.form.get("username"), request.form.get("email"), session.get("c_id")]).fetchall()
        if len(v) > 0:
            db.close()
            return apology("Username/Email already exists in the company database")

        db.execute("INSERT INTO users (c_id, username, email, hash, role) VALUES(?, ?, ?, ?, ?)", user)
        db.commit()
        db.close()
        flash('User added')
        return redirect("/")

@app.route("/inspection", methods=["GET", "POST"])
@login_required
def inspection():
    """Buy shares of stock"""

    if request.method == "GET":
        if not request.args.get("vehicle"):
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number", [session.get("c_id")]).fetchall())
            db.close()
            if len(vehicles) == 1:
                return redirect("/inspection?vehicle=" + str(vehicles[0]["number"]))
            else:
                return render_template("inspection.html", vehicles=vehicles)

        else:
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            v = as_dict(db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?",
                                    [request.args.get("vehicle"), session.get("c_id")]).fetchall())
            oil = db.execute("SELECT next_oil FROM inspections WHERE v_id = ? ORDER BY date DESC", [v[0]["v_id"]]).fetchone()
            db.close()
            if len(v) != 1:
                return redirect("/inspection")
            else:
                return render_template("inspection.html", inspection=c1, vehicle=request.args.get("vehicle"),
                                        v=v[0], oil=oil, date=datetime.date.today().strftime('%Y-%m-%d'))

    else:
        if "" in [request.form.get("v"), request.form.get("miles"), request.form.get("maintenance"), request.form.get("date")]:
            return apology("Missing data")
        query = "INSERT INTO inspections (c_id, u_id, v_id, miles, next_oil, date"
        cols = ""
        values = "(?, ?, ?, ?, ?, ?"
        vars = [session.get("c_id"), session.get("user_id"),
                request.form.get("v"), request.form.get("miles"),
                request.form.get("maintenance"), request.form.get("date")]
        for d in c1:
            if request.form.get(d[0]):
                cols += ", " + d[0]
                values += ", ?"
                vars.append(request.form.get(d[0]))
            if request.form.get(d[1]):
                cols += ", " + d[1]
                values += ", ?"
                vars.append(request.form.get(d[1]))
            if request.form.get(d[2]):
                cols += ", " + d[2]
                values += ", ?"
                vars.append(request.form.get(d[2]))

        query += cols + ") VALUES" + values + ")"
        db = sqlite3.connect(db_path)
        db.execute(query, vars)
        db.commit()
        db.close()

        flash('Inspection loaded into database!')
        return redirect("/")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change Password"""
    if request.method == "GET":
        return render_template("password.html")

    else:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        user = as_dict(db.execute("SELECT * FROM users WHERE u_id = ?", [session.get("user_id")]).fetchall())
        db.close()

        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        if not check_password_hash(user[0]["hash"], request.form.get("old-password")):
            return apology("Wrong password")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confimation don't match")

        hashed_password = generate_password_hash(request.form.get("password"))
        db = sqlite3.connect(db_path)
        db.execute("UPDATE users SET hash = ? WHERE u_id = ?", [hashed_password, session.get("user_id")])
        db.commit()
        db.close()
        flash('Password changed!')
        return redirect("/")


@app.route("/edit-vehicle", methods=["GET", "POST"])
@login_required
def edit_vehicle():
    """Edit a Vehicle already in the database"""

    if request.method == "GET":
        if not request.args.get("vehicle"):
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number", [session.get("c_id")]).fetchall())
            db.close()
            if len(vehicles) == 1:
                return redirect("edit-vehicle?vehicle=" + str(vehicles[0]["number"]))
            else:
                return render_template("edit-vehicle.html", vehicles=vehicles)

        else:
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            v = as_dict(db.execute("SELECT * FROM vehicles WHERE number = ? AND c_id = ?",
                                    [request.args.get("vehicle"), session.get("c_id")]).fetchall())
            db.close()
            if len(v) == 0:
                return redirect("/edit-vehicle")
            else:
                return render_template("edit-vehicle.html", vehicle=request.args.get("vehicle"), v=v[0])

    else:
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        vehicle = [ request.form.get("make"),
                    request.form.get("model"),
                    request.form.get("year"),
                    request.form.get("number"),
                    request.form.get("tag") ]

        db = sqlite3.connect(db_path)
        v_id = db.execute("SELECT v_id FROM vehicles WHERE number = ? AND c_id = ?",
                            [request.form.get("v"), session.get("c_id")]).fetchone()
        if len(v_id) != 1:
            db.close()
            return apology("something went wrong with that request")

        vehicle.append(v_id[0])
        db.execute("UPDATE vehicles SET make = ?, model = ?, year = ?, number = ?, tag = ? WHERE v_id = ?", vehicle)
        db.commit()
        db.close()

        flash('Database Updated!')
        return redirect("/")


@app.route("/edit-user", methods=["GET", "POST"])
@permissions_required
@login_required
def edit_user():
    """Edit a user already in the database"""

    if request.method == "GET":
        if not request.args.get("user"):
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            users = as_dict(db.execute('''SELECT * FROM users WHERE c_id = ? AND role != "owner"''', [session.get("c_id")]).fetchall())
            db.close()
            if len(users) == 1:
                return redirect("/edit-user?user=" + str(users[0]["username"]))
            else:
                return render_template("edit-user.html", users=users)

        else:
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            u = as_dict(db.execute("SELECT * FROM users WHERE username = ?", [request.args.get("user")]).fetchall())
            c = as_dict(db.execute("SELECT * FROM companys WHERE id = ?", [session.get("c_id")]).fetchall())
            db.close()
            if c[0]["owner"] == request.args.get("user"):
                return apology("Can't edit the owner")
            if len(u) != 1:
                return redirect("/edit-user")
            else:
                return render_template("edit-user.html", user=request.args.get("user"), u=u[0])

    else:
        checks = check_inputs(request.form)
        if checks[0]:
            return apology("must provide " + checks[1])

        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        u = as_dict(db.execute("SELECT * FROM users WHERE u_id = ?", [request.form.get("u")]).fetchall())
        others = as_dict(db.execute("SELECT * FROM users WHERE u_id != ? AND c_id = ?",
                            [request.form.get("u"), session.get("c_id")]).fetchall())
        db.close()
        if len(u) != 1:
            return apology("something went wrong with that request")

        for other in others:
            if u[0]["username"] == other["username"] or u[0]["email"] == other["email"]:
                return apology("username/email already in company database")

        if u[0]["role"] == "owner" and request.form.get("role") != "owner":
            return apology("can't change role of the owner")

        if request.form.get("role") not in ["admin", "user"]:
            return apology("wrong role")

        if check_password(request.form.get("password")):
            return apology("password does not meet requirements")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation don't match")

        user = [ request.form.get("username"),
                    request.form.get("email"),
                    generate_password_hash(request.form.get("password")),
                    request.form.get("role"),
                    request.form.get("u")]

        db = sqlite3.connect(db_path)
        db.execute("UPDATE users SET username = ?, email = ?, hash = ?, role = ? WHERE u_id = ?", user)
        db.commit()
        db.close()

        flash('Database Updated!')
        return redirect("/")


@app.route("/vehicles", methods=["GET", "POST"])
@permissions_required
@login_required
def vehicles():
    """View Vehicles"""

    if request.method == "GET":
        if not request.args.get("vehicle"):
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicles = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number", [session.get("c_id")]).fetchall())
            inspections = as_dict(db.execute("SELECT * FROM inspections WHERE c_id = ? ORDER BY date DESC", [session.get("c_id")]).fetchall())
            db.close()

            # Fancy way of creating a dictionary with the vehicles as keys and a list of inspections as values
            v = {ve["number"]:[[i["next_oil"], i["miles"], i["date"]] for i in inspections if i["v_id"] == ve["v_id"]] for ve in vehicles}
            for vehicle, i in v.items():
                if len(i) < 2:
                    i.append(["No data", "No data", "No data", "No data"])
                else:
                    d1 = datetime.datetime.strptime(i[0][2], '%Y-%m-%d')
                    d2 = datetime.datetime.strptime(i[1][2], '%Y-%m-%d')
                    delta_t = abs((d2 - d1).days)
                    delta_m = i[0][1] - i[1][1]
                    remaining = i[0][0] - i[0][1]
                    try:    #avoid deviding by 0
                        day = remaining * delta_t // delta_m
                    except:
                        delta = datetime.timedelta(days = 730)
                        new_date = d1 + delta
                        i[0].append(new_date.strftime('%Y-%m-%d'))
                    else:
                        delta = datetime.timedelta(days = day)
                        new_date = d1 + delta
                        i[0].append(new_date.strftime('%Y-%m-%d'))
            return render_template("vehicles.html", vehicles=v)
        else:
            db = sqlite3.connect(db_path)
            db.row_factory = sqlite3.Row
            vehicle = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? AND number = ?",
                                    [session.get("c_id"), request.args.get("vehicle")]).fetchall())
            if len(vehicle) != 1:
                return redirect("/vehicles")
            v = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number",
                                    [session.get("c_id")]).fetchall())
            inspections = as_dict(db.execute("SELECT * FROM inspections WHERE c_id = ? AND v_id = ? ORDER BY date DESC, i_id DESC",
                                                [session.get("c_id"), vehicle[0]["v_id"]]).fetchall())
            users = as_dict(db.execute("SELECT * FROM users WHERE c_id = ?", [session.get("c_id")]).fetchall())
            db.close()

            inspection = [[i[c[1]], c[3], i["date"], u["username"]] for i in inspections
                            for c in c1 for u in users if i[c[0]] == 0 and u["u_id"] == i["u_id"]]
            if len(inspection) < 1:
                inspection = [["No data", "No data", "No data", "No data"]]
            return render_template("vehicles.html", vehicle=request.args.get("vehicle"), inspection=inspection, vehicles=v)
    else:
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        vehicle = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? AND number = ?",
                                [session.get("c_id"), request.form.get("vehicle")]).fetchall())
        if len(vehicle) != 1:
            return redirect("/vehicles")
        v = as_dict(db.execute("SELECT * FROM vehicles WHERE c_id = ? ORDER BY number",
                                [session.get("c_id")]).fetchall())
        inspections = as_dict(db.execute("SELECT * FROM inspections WHERE c_id = ? AND v_id = ? ORDER BY date DESC, i_id DESC",
                                            [session.get("c_id"), vehicle[0]["v_id"]]).fetchall())
        users = as_dict(db.execute("SELECT * FROM users WHERE c_id = ?", [session.get("c_id")]).fetchall())
        db.close()
        inspection = [[i[c[1]], c[3], i["date"], u["username"]] for i in inspections
                        for c in c1 for u in users if i[c[0]] == 0 and u["u_id"] == i["u_id"]]
        if len(inspection) < 1:
                inspection = [["No data", "No data", "No data", "No data"]]
        return jsonify(inspection)