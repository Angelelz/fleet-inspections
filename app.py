import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Handle requests to the root


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    if not session["user_id"]:
        return redirect("/login")

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    stocks = db.execute("SELECT * FROM stocks WHERE user_id = ?", session["user_id"])
    stock_prices = []
    total_value = 0
    for stock in stocks:
        stock_price = lookup(stock["stock"])["price"]
        stock_prices.append(stock_price)
        total_value += (stock_price * stock["quantity"])
    total_value += user[0]["cash"]

    return render_template("index.html", user=user, stocks=stocks, prices=stock_prices, value=total_value, number=len(stocks))

# Handle the requests to /buy


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if not session["user_id"]:
        return redirect("/login")

    user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    if request.method == "GET":
        stock = request.args.get("stock")
        # Passing cash to tell the user how much he has to spend, and the stock in case coming from index.html
        return render_template("buy.html", cash=user[0]["cash"], stock=stock)

    else:
        stock = request.form.get("symbol")
        if not stock:
            return apology("Stock not found")

        stock = lookup(stock)
        if not stock:
            return apology("Stock not found")

        quantity = request.form.get("shares")
        if not quantity.isdigit() or int(quantity) < 1:
            return apology("Quantity is not a positive integer")

        quantity = int(quantity)
        if stock["price"] * quantity > user[0]["cash"]:
            return apology("Not enought money")

        new_cash = user[0]["cash"] - (stock["price"] * quantity)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, user[0]["id"])
        db.execute("INSERT INTO transactions (user_id, t_type, stock, quantity, price,\
                   timestamp) VALUES(?, ?, ?, ?, ?, ?)",
                   user[0]["id"], "buy", stock["symbol"], quantity, stock["price"], datetime.datetime.now())
        owned_stocks = db.execute("SELECT stock, quantity FROM stocks WHERE user_id = ? AND stock = ?",
                                  user[0]["id"], stock["symbol"])
        if len(owned_stocks) > 0:
            new_value = owned_stocks[0]["quantity"] + quantity
            db.execute("UPDATE stocks SET quantity = ? WHERE user_id = ? AND stock = ?", new_value, user[0]["id"], stock["symbol"])

        else:
            db.execute("INSERT INTO stocks (user_id, stock, quantity) VALUES(?, ?, ?)", user[0]["id"], stock["symbol"], quantity)
        flash('Transaction Performed Successfully!')
        return redirect("/")

# To show the transaction history for the user


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])
    number = len(transactions)
    prices = []
    for t in transactions:
        prices.append(t["price"])
    return render_template("history.html", transactions=transactions, number=number, prices=prices)

# Logs user in


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        db.execute("CREATE TABLE IF NOT EXISTS transactions \
                    (t_id INTEGER PRIMARY KEY, user_id INTEGER,\
                    t_type TEXT NOT NULL, stock TEXT NOT NULL,\
                    quantity INTEGER NOT NULL, price REAL NOT NULL,\
                    timestamp TEXT NOT NULL, FOREIGN KEY (user_id)\
                    REFERENCES users (id) ON DELETE CASCADE \
                    ON UPDATE NO ACTION)")
        db.execute("CREATE TABLE IF NOT EXISTS stocks \
                    (s_id INTEGER PRIMARY KEY, user_id INTEGER,\
                    stock TEXT NOT NULL, quantity INTEGER NOT NULL,\
                    FOREIGN KEY (user_id)\
                    REFERENCES users (id) ON DELETE CASCADE \
                    ON UPDATE NO ACTION)")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# Logs user out


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash('You logged out')
    return render_template("login.html")

# Check for a stock's price


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    else:
        quoted = lookup(request.form.get("symbol"))
        if not quoted:
            return apology("Symbol not found")

        return render_template("quoted.html", name=quoted["name"], price=usd(quoted["price"]))

# Register a new user


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        name = request.form.get("username")
        if not request.form.get("username"):
            return apology("must provide username")

        usernames = db.execute("SELECT username FROM users WHERE username IS ?", name)
        if len(usernames) > 0:
            return apology("username already taken")

        if not request.form.get("password"):
            return apology("must provide password")

        if not request.form.get("confirmation"):
            return apology("must provide a confirmation")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match")

        hashed_password = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", name, hashed_password)

        flash('User registered')
        return render_template("login.html")

# Lets user sell his/her stocks


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        if not session["user_id"]:
            return redirect("/login")

        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        stocks = db.execute("SELECT * FROM stocks WHERE user_id = ?", session["user_id"])
        stock_list = []
        for stock in stocks:
            stock_list.append(stock["stock"])

        stock = request.args.get("stock")
        return render_template("sell.html", stocks=stock_list, number=len(stock_list), stock=stock)

    else:
        stock = request.form.get("symbol")
        if not stock:
            return apology("You didn't provide any stock")

        stock = lookup(stock)
        if not stock:
            return apology("Stock not found")

        quantity = request.form.get("shares")
        if not quantity.isdigit() or int(quantity) < 1:
            return apology("Quantity is not a positive integer")

        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        stocks = db.execute("SELECT * FROM stocks WHERE user_id = ? AND stock = ?", session["user_id"], stock["symbol"])

        if len(stocks) != 1:
            return apology("You don't own that stock")

        quantity = int(quantity)
        if quantity > stocks[0]["quantity"]:
            return apology("You can't sell more stocks than you own")

        new_cash = user[0]["cash"] + (stock["price"] * quantity)
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, user[0]["id"])
        db.execute("INSERT INTO transactions (user_id, t_type, stock, quantity, price,\
                   timestamp) VALUES(?, ?, ?, ?, ?, ?)",
                   user[0]["id"], "sell", stock["symbol"], quantity, stock["price"], datetime.datetime.now())

        new_quantity = stocks[0]["quantity"] - quantity
        if new_quantity < 1:
            db.execute("DELETE FROM stocks WHERE stock = ?", stock["symbol"])

        else:
            db.execute("UPDATE stocks SET quantity = ? WHERE user_id = ? AND stock = ?",
                       new_quantity, user[0]["id"], stock["symbol"])

        flash('Transaction Performed Successfully!')
        return redirect("/")

# Let user change password


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change Password"""
    if request.method == "GET":
        return render_template("password.html")

    else:
        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
        if not request.form.get("old-password"):
            return apology("must provide old password")

        if not check_password_hash(user[0]["hash"], request.form.get("old-password")):
            return apology("Wrong password")

        if not request.form.get("password"):
            return apology("must provide password")

        if not request.form.get("confirmation"):
            return apology("must provide a confirmation")

        print(request.form.get("password"))
        print(request.form.get("confirmation"))
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confimation don't match")

        hashed_password = generate_password_hash(request.form.get("password"))
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hashed_password, session["user_id"])

        flash('Password changed!')
        return redirect("/")

# Lets user add cash to their account


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Add cash"""
    if request.method == "GET":
        return render_template("cash.html")

    else:
        if not request.form.get("amount"):
            return apology("must insert amount")

        try:
            quantity = float(request.form.get("amount"))
        except:
            return apology("Quantity is not a number")

        if quantity < 0.01:
            return apology("Quantity is not positive")

        if quantity > 10000:
            return apology("Quantity is bigger that $10,000.00")

        user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        db.execute("UPDATE users SET cash = ? WHERE id = ?", user[0]["cash"] + quantity, session["user_id"])

        db.execute("INSERT INTO transactions (user_id, t_type, stock, quantity, price,\
                   timestamp) VALUES(?, ?, ?, ?, ?, ?)",
                   user[0]["id"], "Added Cash", "N/A", 1, quantity, datetime.datetime.now())

        flash('You added cash to your account')
        return redirect("/")