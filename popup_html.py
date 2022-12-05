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
    <thead>
    <tr>
        <th class="tg-0pky">Occupation: """+ occupation +"""</th>
    </tr>
    </thead>
    <tbody>
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



