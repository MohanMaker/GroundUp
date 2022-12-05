# username = groundup
# password = groundup
# Implement map
# Implement location filtering
# Implement other filtering

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import folium
import geopandas
import geopy
import sys

from popup_html import popup_html
from helpers import reversegeocode, geocode, apology, login_required, lookup

# Configure application
app = Flask(__name__)

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        # Get inputs from user
        distance = request.form.get("distance")
        address = request.form.get("address")
        occupation = request.form.get("occupation")
        education = request.form.get("education")
        sector = request.form.get("sector")

        lat, lng = geocode(address)
        radius = geopy.units.degrees(arcminutes=geopy.units.nautical(miles=int(distance)))
        latmin = lat - radius
        latmax = lat + radius
        lngmin = lng - radius
        lngmax = lng + radius

        addtofiltered = db.execute("SELECT * FROM datacollectors WHERE occupation = ? AND education = ? AND sector = ? AND (lat BETWEEN ? AND ?) AND (lng BETWEEN ? AND ?);", occupation, education, sector, latmin, latmax, lngmin, lngmax)

        for row in addtofiltered:
            db.execute("INSERT INTO filtered (firstname, lastname, lat, lng, occupation, education, sector) VALUES (?, ?, ?, ?, ?, ?, ?);", row["firstname"], row["lastname"], row["lat"], row["lng"], row["occupation"], row["education"], row["sector"])

        return redirect("/map")
    else:
        occupation = db.execute("SELECT DISTINCT occupation FROM datacollectors;")
        education = db.execute("SELECT DISTINCT education FROM datacollectors;")
        sector = db.execute("SELECT DISTINCT sector FROM datacollectors;")
        return render_template("index.html", occupation=occupation, education=education, sector=sector)

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

        return render_template("quoted.html", name=info["name"], symbol=info["symbol"], price=info["price"])
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

@app.route("/map")
@login_required
def map_endpoint():
    # initialize folium map. Sets initial location to India. Also uses leaflet and OpenStreetMaps. 
    myMap = folium.Map(location=[28.6139, 77.2090],
            zoom_start=6,
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='Attribution to OpenStreetMaps')    

    # Retrieve the location from our sql table filtered. This outputs in the form of a list of dictionaries.
    collector_info = db.execute("SELECT * FROM filtered;")

    # Create a for loop that iterates through our list of dictionaries. Retrieves values from the x and y coordinate respectively.
    # Then, inputs the x and y coordinates into the map using the folium.Marker functionality.
    for item in collector_info:
        x = item["lat"]
        y = item["lng"]

        # uses the popup_html helper function to create the "profiles" when you click on the marker
        html = popup_html(item)
        popup = folium.Popup(folium.Html(html, script=True), max_width=500)

        # Creates the markers at the desired location with the correct popups
        folium.Marker([x, y], popup=popup).add_to(myMap)

    # Saves the changes on the html page. 
    myMap.save("templates/map2.html")

    # Delete all elements from filtered table so you can graph more things in the future
    db.execute("DELETE FROM filtered;")
    return render_template("map2.html")