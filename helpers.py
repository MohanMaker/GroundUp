from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="geoapiExercises")

from flask import redirect, render_template, session
from functools import wraps

def reversegeocode(lat, lng):
    lat, lng = str(lat), str(lng)
    try:
        location = geolocator.reverse(lat+","+lng)
        address = location.raw['address']
        
        # traverse the data
        output = {}
        output['city'] = address.get('city', '')
        output['state'] = address.get('state', '')
        output['country'] = address.get('country', '')
        output['zipcode'] = address.get('postcode')
    except:
        return 1;
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
    return render_template("apology.html", top=code, bottom=message), code


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
