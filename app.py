# username = groundup
# password = groundup

import os
import sys
from tempfile import mkdtemp

import folium
import geopandas
import geopy
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import apology, geocode, login_required, lookup, reversegeocode
from popup_html import popup_html

# Configure application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
        occupation = str(request.form.get("occupation"))
        degree = str(request.form.get("degree"))
        sector = str(request.form.get("sector"))

        if geocode(address) == 1:
            apology("Unrecognized location", 403) 
        lat, lng = geocode(address)
        radius = geopy.units.degrees(arcminutes=geopy.units.nautical(miles=int(distance)))
        latmin = lat - radius
        latmax = lat + radius
        lngmin = lng - radius
        lngmax = lng + radius

        # Add contents selected by filters into filtered table to graph
        db.execute("INSERT INTO datacollectorsfiltered SELECT * FROM datacollectors WHERE occupation = ? AND degree = ? AND sector = ? AND (lat BETWEEN ? AND ?) AND (lng BETWEEN ? AND ?);", occupation, degree, sector, latmin, latmax, lngmin, lngmax)

        return redirect("/map")
    else:
        occupation = db.execute("SELECT DISTINCT occupation FROM datacollectors;")
        degree = db.execute("SELECT DISTINCT degree FROM datacollectors;")
        sector = db.execute("SELECT DISTINCT sector FROM datacollectors;")
        return render_template("index.html", occupation=occupation, degree=degree, sector=sector)

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

    if db.execute("SELECT COUNT(*) FROM datacollectorsfiltered;")[0]['COUNT(*)'] != 0:
        # Retrieve the appropriate data collectors based on our filters. This outputs in the form of a list of dictionaries. 
        collector_info = db.execute("SELECT * FROM datacollectorsfiltered;")
    else:
        # If we have not applied filters, show all of the data collectors
        collector_info = db.execute("SELECT * FROM datacollectors;")

    # find center lat and lng of the points to graph
    count = 0
    latsum = 0
    lngsum = 0
    for row in collector_info:
        latsum += row["lat"]
        lngsum += row["lng"]
        count += 1
    avglat = latsum / count
    avglng = lngsum / count

    # initialize folium map. Sets initial location to India. Also uses leaflet and OpenStreetMaps. 
    myMap = folium.Map(location=[avglat, avglng], 
            width='100%',
            height='90%',
            zoom_start=6,
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='Attribution to OpenStreetMaps')    
        
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

    # Delete all elements from filtered data collectors table so things map can be generated again in the future.
    db.execute("DELETE FROM datacollectorsfiltered;")

    return redirect("/full_map")


@app.route("/full_map")
@login_required
def full_map_page():
    return render_template("map.html")