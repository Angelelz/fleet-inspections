from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def permissions_required(f):
    """
    Decorate routes to require permissions "owner" or "admin".

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None or session.get("role") is None or session.get("role") not in ["owner", "admin"]:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def check_password(password):
    '''Check if password follows requirements'''
    if password:
        return False
    else:
        return True

def as_dict(rows):
    '''Return a list of dictionaries to be user to query the db'''
    return list(map(dict,rows))

def check_inputs(obj, array = [], ignore = True):
    '''Check if the inputs are blank or none with the option to pass
        in an array to either ignore or to just enforce the ones provided'''
    for key in obj.keys():
        if ignore:
            if  key not in array and (not obj.get(key) or obj.get(key) == ""):
                return [True, key]
        else:
            if key in array and (not obj.get(key) or obj.get(key) == ""):
                return [True, key]

    return [False, ""]


def best_fit(X, Y, y):
    """Calculate the best fit line for a set of point (X, Y) and returns the corresponding value x for the y provided"""
    if len(X) == 0 or len(Y) == 0 or not y:
        return 0
    xbar = sum(X)/len(X)
    ybar = sum(Y)/len(Y)
    n = len(X) # or len(Y)

    numer = sum(xi*yi for xi,yi in zip(X, Y)) - n * xbar * ybar
    denum = sum(xi**2 for xi in X) - n * xbar**2

    if denum == 0:
        return 0

    b = numer / denum
    a = ybar - b * xbar

    return (y - a) / b