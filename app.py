# username = groundup
# password = groundup
# Implement map
# Implement location filtering
# Implement other filtering

# Search page
# Dropdowns
# Map page 
# Show unfiltered map

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///groundup.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    portfolio = db.execute("SELECT * FROM portfolio WHERE id = ?", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]

    total = cash
    if len(portfolio) == 0:
        portfolio = None
    else:
        sharesvalue = 0
        for row in portfolio:
            stock = lookup(row["symbol"])
            row["persymbolprice"] = stock["price"]
            row["totalsymbolvalue"] = (row["persymbolprice"] * row["shares"])
            sharesvalue += row["totalsymbolvalue"]
        total += sharesvalue
    return render_template("index.html", portfolio=portfolio, cash=cash, total=total)


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
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")

        if symbol == '':
            return apology("Missing symbol", 400)

        info = lookup(symbol)
        if info == None:
            return apology("Invalid symbol", 400)

        return render_template("quoted.html", name=info["name"], symbol=info["symbol"], price=usd(info["price"]))
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get username and password from user
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate username
        if username == '' or len(db.execute("SELECT * FROM users WHERE username = ?", username)) != 0:
            return apology("Enter a valid username", 400)

        # Validate password
        if password == '' or confirmation == '' or password != confirmation:
            return apology("Enter a valid password", 400)

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?);", username, generate_password_hash(password))

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")