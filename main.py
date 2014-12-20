import json
from flask import Flask, jsonify
from models import User

from google.appengine.ext import db

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return 'PyCharm e stato scritto da un piccione'


@app.route('/list')
def user_list():
    users = db.GqlQuery('SELECT * FROM User '
                        'ORDER BY name DESC').fetch(10)
    return json.dumps([user.to_dict() for user in users])


@app.route('/add')
def add():
    """Add Claudio"""
    obj = User(name='Claudio')
    obj.put()

    return 'Aggiunto Claudio'


@app.route('/test')
def print_json_test():
    json_test = """[{"id":0, "Titolo":"Viaggio al centro della Terra (Film)", "Orario":"21:30", "Canale":"Rai 3", "Numero":3},{ "id":1, "Titolo":"K19 - The widowmaker (Film)", "Orario":"21:15", "Canale":"Rai Movie", "Numero":24},{ "id":2, "Titolo":"Natale a 4 zampe (Film)", "Orario":"21:11", "Canale":"Canale 5", "Numero":5},{ "id":3, "Titolo":"Alla ricerca della stella del Natale (Film)", "Orario":"21:25", "Canale":"Italia 1", "Numero":6},{ "id":4, "Titolo":"Il risolutore - A Man Apart (Film)", "Orario":"21:29", "Canale":"Rete 4", "Numero":4},{ "id":5, "Titolo":"Le comiche 2 (Film)", "Orario":"21:00", "Canale":"Iris", "Numero":22},{ "id":6, "Titolo":"Brivido biondo (Film)", "Orario":"21:11", "Canale":"Italia 2", "Numero":35},{ "id":7, "Titolo":"Il presidente - Una storia d'amore (Film)", "Orario":"21:10", "Canale":"La 5", "Numero":30},{ "id":8, "Titolo":"Laure (Film)", "Orario":"21:10", "Canale":"Cielo", "Numero":26},{ "id":9, "Titolo":"Il piccolo lord (Film)", "Orario":"21:15", "Canale":"Rai Premium", "Numero":25},{ "id":10, "Titolo":"La parola ai giurati (Film)", "Orario":"21:10", "Canale":"La7", "Numero":7},{ "id":11, "Titolo":"Lupo mannaro (Film)", "Orario":"20:40", "Canale":"ClassTV", "Numero":27}"]"""
    return json_test


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
