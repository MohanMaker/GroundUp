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
from helpers import geocode, reversegeocode, login_required, apology
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

        # Remember what type of user is logged in (collector or client)
        session["type"] = rows[0]["type"]

        # create a new empty data collector linked to the user (if the user is a data collector)
        if session["type"] == 'collector':
            userid = session["user_id"]
            db.execute("INSERT INTO datacollectors (userid) VALUES (?);", userid)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get username and password from user
        username = request.form.get("username")
        new_password = request.form.get("password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
            
        # Ensure username exists
        if len(rows) != 1:
            return apology("invalid username", 403)

        db.execute("UPDATE users SET hash = ? WHERE username = ?", generate_password_hash(new_password), username)

        return redirect("/")
        
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
            return apology("enter a valid username", 400)

        # Validate password
        if password == '' or confirmation == '' or password != confirmation:
            return apology("enter a valid password", 400)

        if request.form['submit'] == 'collector':
            type = 'collector';
        else:
            type = 'client'

        db.execute("INSERT INTO users (username, hash, type) VALUES(?, ?, ?);", username, generate_password_hash(password), type)

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if session.get("type") == 'client':
        if request.method == "POST":
            # submit results of form to database

            # Get inputs from user
            distance = request.form.get("distance")
            address = request.form.get("address")
            occupation = str(request.form.get("occupation"))
            degree = str(request.form.get("degree"))
            sector = str(request.form.get("sector"))

            if distance == "" or address == "":
                pass
            elif geocode(address) == 1:
                return apology("unrecognized location", 403) 
            else:
                lat, lng = geocode(address)
                radius = geopy.units.degrees(arcminutes=geopy.units.nautical(miles=int(distance)))
                latmin = lat - radius
                latmax = lat + radius
                lngmin = lng - radius
                lngmax = lng + radius

            # Append to datacollectors filtered based on the inputs from the user, handling blank inputs
            select = "INSERT INTO datacollectorsfiltered SELECT id, firstname, lastname, lat, lng, occupation, degree, sector FROM datacollectors"
            first = 0

            def fillerchars(first, select):
                if first == 0:
                    select += " WHERE"
                if first == 1:
                    select += " AND"
                first = 1
                return first, select

            if occupation != "None":
                first, select = fillerchars(first, select)
                select += " occupation = ?"
            else:
                first, select = fillerchars(first, select)
                select += " occupation IS NOT NULL"
            if degree != "None":
                first, select = fillerchars(first, select)
                select += " degree = ?"
            else:
                first, select = fillerchars(first, select)
                select += " degree IS NOT NULL"
            if sector != "None":
                first, select = fillerchars(first, select)
                select += " sector = ?"
            else:
                first, select = fillerchars(first, select)
                select += " sector IS NOT NULL"
            if distance == "" or address == "":
                first, select = fillerchars(first, select)
                select += " lat IS NOT NULL AND lng IS NOT NULL"
            else:
                first, select = fillerchars(first, select)
                select += " (lat BETWEEN ? AND ?) AND (lng BETWEEN ? AND ?)"

            arguments = []
            if occupation != "None":
                arguments.append(occupation)
            if degree != "None":
                arguments.append(degree)
            if sector != "None":
                arguments.append(sector)
            if not(distance == "" or address == ""):
                arguments.append(latmin)
                arguments.append(latmax)
                arguments.append(lngmin)
                arguments.append(lngmax)
            arguments = tuple(arguments)
            
            # Add contents selected by filters into filtered table to graph
            db.execute(select, *arguments)

            return redirect("/map")
        else:
            # set up the form to be filled out
            occupation = db.execute("SELECT DISTINCT occupation FROM datacollectors WHERE occupation IS NOT NULL;")
            degree = db.execute("SELECT DISTINCT degree FROM datacollectors WHERE degree IS NOT NULL;")
            sector = db.execute("SELECT DISTINCT sector FROM datacollectors WHERE sector IS NOT NULL;")
            return render_template("client.html", occupation=occupation, degree=degree, sector=sector)

    elif session.get("type") == 'collector':
        userid = session["user_id"]
        if request.method == "POST":
            if request.form['updatebtn'] == 'name':
                firstname = str(request.form.get("firstname"))
                lastname = str(request.form.get("lastname"))
                db.execute("UPDATE datacollectors SET firstname = ?, lastname = ? WHERE userid = ?;", firstname, lastname, userid)

            elif request.form['updatebtn'] == 'location':
                lat = request.form.get("latitude")
                lng = request.form.get("longitude")

                #check that lat and lng are valid
                if reversegeocode(lat, lng) == 1:
                    return apology("enter a valid lat and lng", 403)

                db.execute("UPDATE datacollectors SET lat = ?, lng = ? WHERE userid = ?;", lat, lng, userid)
            elif request.form['updatebtn'] == 'occupation':
                occupation = str(request.form.get("occupation"))
                db.execute("UPDATE datacollectors SET occupation = ? WHERE userid = ?;", occupation, userid)
            elif request.form['updatebtn'] == 'degree':
                degree = str(request.form.get("degree"))
                db.execute("UPDATE datacollectors SET degree = ? WHERE userid = ?;", degree, userid)
            elif request.form['updatebtn'] == 'sector':
                sector = str(request.form.get("sector"))
                db.execute("UPDATE datacollectors SET sector = ? WHERE userid = ?;", sector, userid)
            return redirect("/")
        else:
            profile = db.execute("SELECT * FROM datacollectors WHERE userid = ?;", userid)
            address = reversegeocode(profile[0]["lat"], profile[0]["lng"])
            username = db.execute("SELECT username FROM users WHERE id = ?", userid)[0]["username"]
            return render_template("collector.html", profile=profile, address=address, username=username)

@app.route("/map")
@login_required
def map_endpoint():
    
    # Retrieve the appropriate data collectors based on our filters. This outputs in the form of a list of dictionaries. 
    collector_info = db.execute("SELECT * FROM datacollectorsfiltered WHERE lat IS NOT NULL AND lng is NOT NULL;")

    # find center lat and lng of the points to graph
    count = 0
    latsum = 0
    lngsum = 0
    for row in collector_info:
        latsum += row["lat"]
        lngsum += row["lng"]
        count += 1
    # handle if there are no data collectors
    if count == 0:
        avglat = 22.991144554354932
        avglng = 79.70703619196892
    else:
        avglat = latsum / count
        avglng = lngsum / count

    # initialize folium map. Sets initial location to India. Also uses leaflet and OpenStreetMaps. 
    myMap = folium.Map(location=[avglat, avglng], 
            width='100%',
            height='100%',
            zoom_start=6,
            position='relative')    
        
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
    myMap.save("templates/mapdata.html")

    # Delete all elements from filtered data collectors table so things map can be generated again in the future.
    db.execute("DELETE FROM datacollectorsfiltered;")

    return render_template("map.html")