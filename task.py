from flask import Flask
from IMDB_retriever import retrieve_movie
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/task/suggest/')
def random_suggest():
    """
    Send a random movie suggest for all users.
    :return: simple confirmation string
    :rtype string
    """
    users = User.query()  # Get all users

    for user in users.iter():
        send_suggestion(user, random_movie_selection(result_movies_schedule("free", "today")))  # Send suggest for user

    return "Suggestions sended"


@app.route('/task/retrieve/')
def retrieve():
    """

    :return:
    """
    movies = result_movies_schedule("free", "today")
    for movie in movies:
        movie_title = movie['originalTitle'].encode('utf-8') if movie['originalTitle'] is not None else movie[
            'title'].encode('utf-8')  # Retrieve movie title

        retrieve_movie(movie_title)  # Retrieve movie from IMDB by title and store in the datastore

    return 'Movies of today retrieved'