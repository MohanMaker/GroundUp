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


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        # Get symbol and shares from user
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate symbol
        if not symbol:
            return apology("Missing symbol", 400)
        stock = lookup(symbol)
        if stock == None:
            return apology("Invalid symbol", 400)

        # Validate shares
        if not shares.isnumeric() or int(shares) <= 0 or int(shares) % 1 != 0:
            return apology("Shares must be a positive integer", 400)
        shares = int(shares)

        # Check for sufficient funds
        userbalance = db.execute("SELECT cash FROM users WHERE id = ?;", session["user_id"])
        cash = userbalance[0]["cash"] - stock["price"] * shares
        if cash < 0:
            return apology("Can't afford at current price", 400)

        # Update databases
        # Update cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, session["user_id"])
        # Update portfolio
        pastpurchase = db.execute("SELECT * FROM portfolio WHERE id = ? AND symbol = ?;", session["user_id"], stock["symbol"])
        if len(pastpurchase) != 0:
            shares = shares + pastpurchase[0]["shares"]
            db.execute("UPDATE portfolio SET shares = ? WHERE id = ? AND symbol = ?;", shares, session["user_id"], stock["symbol"])
        else:
            db.execute("INSERT INTO portfolio (id, symbol, name, shares) VALUES (?, ?, ?, ?);",
                       session["user_id"], stock["symbol"], stock["name"], shares)
        # Update history
        db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (?, ?, ?, ?);",
                   session["user_id"], symbol, shares, stock["price"])

        flash("Bought!")
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    history = db.execute("SELECT * FROM history WHERE id = ?", session["user_id"])
    if len(history) == 0:
        history = None
    return render_template("history.html", history=history)


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

        # Password checking add-on
        if not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            return apology("Enter a password with at least one letter and number", 400)

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?);", username, generate_password_hash(password))

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    symbolsowned = db.execute("SELECT symbol FROM portfolio WHERE id = ?", session["user_id"])
    if request.method == "POST":
        # Get symbol and shares from user
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Validate symbol
        if not symbol:
            return apology("Missing symbol", 400)

        have = False
        for row in symbolsowned:
            if symbol == row["symbol"]:
                have = True
        if have == False:
            return apology("Symbol not owned", 400)

        # Validate shares
        if not shares.isnumeric() or int(shares) <= 0 or int(shares) % 1 != 0:
            return apology("Shares must be a positive integer", 400)
        shares = int(shares)

        # Verify that the user owns enough shares to sell
        sharesowned = db.execute("SELECT shares FROM portfolio WHERE id = ? AND symbol = ?",
                                 session["user_id"], symbol)[0]["shares"]
        sharesowned -= shares
        if sharesowned < 0:
            return apology("Too many shares", 400)

        # Update databases
        stock = lookup(symbol)
        # Update history
        db.execute("INSERT INTO history (id, symbol, shares, price) VALUES (?, ?, ?, ?)",
                   session["user_id"], symbol, (-1 * shares), stock["price"])
        # Update portfolio
        if sharesowned == 0:
            db.execute("DELETE FROM portfolio WHERE id = ? AND symbol = ?;", session["user_id"], symbol)
        else:
            db.execute("UPDATE portfolio SET shares = ? WHERE id = ? AND symbol = ?;", sharesowned, session["user_id"], symbol)
        # Update users cash
        cost = stock["price"] * shares
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", cost, session["user_id"])

        flash("Sold!")
        return redirect("/")
    else:
        return render_template("sell.html", symbolsowned=symbolsowned)