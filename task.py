from requests import ConnectionError
from flask import Flask
from werkzeug.exceptions import BadRequest
from IMDB_retriever import retrieve_movie_from_title
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import RetrieverError, TV_TYPE
from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(60)

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
        send_suggestion(user, random_movie_selection(result_movies_schedule('free', 'today')))  # Send suggest for user

    return 'OK'


@app.route('/task/retrieve/<tv_type>')
def retrieve(tv_type):
    """
    Retrieve movie info from IMDB for all movies from today schedule.
    :return: simple confirmation string
    :rtype string
    """

    if tv_type in TV_TYPE:
        movies = result_movies_schedule(tv_type, 'today')  # Retrieve movies from today schedule
        for movie in movies:
            movie_title = movie['title']
            movie_original_title = movie['originalTitle']
            if movie_original_title is None:
                movie_original_title = movie_title

            try:
                retrieve_movie_from_title(movie_original_title,
                                          movie_title)  # Retrieve movie from IMDB by title and store it
            except ConnectionError:
                print 'ConnectionError, I retry..'
                try:
                    retrieve_movie_from_title(movie_original_title,
                                              movie_title)  # Retrieve movie from IMDB by title and store it
                except Exception:
                    print 'No connection, next one'
                    pass
            except RetrieverError as retriever_error:
                print retriever_error

        return 'OK'
    else:
        raise BadRequest