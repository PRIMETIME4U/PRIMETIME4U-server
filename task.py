from requests import ConnectionError
from flask import Flask
from IMDB_retriever import retrieve_movie
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import RetrieverError

app = Flask(__name__)
app.config['DEBUG'] = True


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
    Retrieve movie info from IMDB for all movies from today schedule.
    :return: simple confirmation string
    :rtype string
    :raise RetrieverError: if there is an error from MYAPIFILMS
    """
    # TODO: retrieve also movie info for sky and premium #22
    # TODO: see how it is possible write error on google dashboard
    movies = result_movies_schedule("free", "today")  # Retrieve movies from today schedule

    for movie in movies:
        movie_title = movie['originalTitle'] if movie['originalTitle'] is not None else movie[
            'title']  # Retrieve movie title

        try:
            retrieve_movie(movie_title)  # Retrieve movie from IMDB by title and store in the datastore
        except ConnectionError:  # Connection error.. then retry
            retrieve_movie(movie_title)
        except RetrieverError:  # There is some problem.. we do not handle it (now)
            pass

    return 'Movies of today retrieved'