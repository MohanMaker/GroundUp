from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="geoapiExercises")

from flask import redirect, render_template, session
from functools import wraps


# Converts lat and lng into address string, returns 1 if failed
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


# Converts adderss string into lat and lng coordinates, returns 1 if failed
def geocode(address):
    try:
        location = geolocator.geocode(address)
        lat = location.latitude
        lng = location.longitude
    except:
        return 1;   

    return lat, lng

def popup_html(item):
    # Retrieve needed information from list of dictionaries
    firstname = item["firstname"]
    lastname = item["lastname"]
    name = firstname + " " + lastname
    occupation = item["occupation"]
    degree = item["degree"]
    sector = item["sector"]

    # put into an html format, this allows it to show up formatted through tables in the html page
    html = """<!DOCTYPE html>
    <html>
    <head>
    <h4 style="margin-bottom:10"; width="200px">"""+ name +"""</h4>
    </head>
        <table style="height: 126px; width: 350px;">
    <tbody>
    <tr>
        <td class="tg-0pky">Occupation: """+ occupation +"""</td>
    </tr>
    <tr>
        <td class="tg-0pky">Degree: """+ degree +"""</td>
    </tr>
    <tr>
        <td class="tg-0pky">Sector: """+ sector +"""</td>
    </tr>

    </tbody>
    </table>
    </html>
    """
    return html

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