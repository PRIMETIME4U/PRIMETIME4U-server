import logging
from flask import Flask
from werkzeug.exceptions import BadRequest
from IMDB_retriever import retrieve_movie_from_title
from google.appengine.api import taskqueue
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import TV_TYPE, RetrieverError

app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/_ah/start/task/suggest/')
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


@app.route('/_ah/start/task/retrieve')
def retrieve():
    """
    Retrieve movie info from IMDB for all movies from today schedule.
    :return: simple confirmation string
    :rtype string
    """
    taskqueue.add(url='/_ah/start/task/retrieve/free', method='GET')
    taskqueue.add(url='/_ah/start/task/retrieve/sky', method='GET')
    taskqueue.add(url='/_ah/start/task/retrieve/premium', method='GET')

    return 'OK'


@app.route('/_ah/start/task/retrieve/<tv_type>', methods=['GET'])
def retrieve_type(tv_type):
    """
    Retrieve movie info from IMDB for all movies from today schedule.
    :return: simple confirmation string
    :rtype string
    """

    if tv_type in TV_TYPE:
        movies = result_movies_schedule(tv_type, 'today')  # Retrieve movies from today schedule
        while len(movies) > 0:
            movie_title = movies[0]['title']
            movie_original_title = movies[0]['originalTitle']
            movie_year = movies[0]['year']
            if movie_original_title is None:
                movie_original_title = movie_title

            try:
                retrieve_movie_from_title(movie_original_title,
                                          movie_year,
                                          movie_title,
                                          movies[0]['movieUrl'])  # Retrieve movie from IMDB by title and store it
            except Exception as exception:
                logging.error("Error in retrieving %s: %s", movie_original_title, exception)
                if type(exception) is RetrieverError:
                    logging.error("Not our error...")
                    movies.pop(0)
                pass
            movies.pop(0)
        return 'OK'
    else:
        raise BadRequest