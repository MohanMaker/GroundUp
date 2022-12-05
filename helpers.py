import os
import requests
import urllib.parse
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="geoapiExercises")

from flask import redirect, render_template, request, session
from functools import wraps

def reversegeocode(lat, lng):
    lat, lng = str(lat), str(lng)
    location = geolocator.reverse(lat+","+lng)
 
    address = location.raw['address']
    
    # traverse the data
    output = {}
    output['city'] = address.get('city', '')
    output['state'] = address.get('state', '')
    output['country'] = address.get('country', '')
    output['zipcode'] = address.get('postcode')

    return output

def geocode(address):
    try:
        location = geolocator.geocode(address)
        lat = location.latitude
        lng = location.longitude
    except:
        return 1;   

    return lat, lng

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
