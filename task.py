from requests import ConnectionError
from flask import Flask
from IMDB_retriever import retrieve_movie_from_title
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import RetrieverError, TV_TYPE

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


@app.route('/task/retrieve/')
def retrieve():
    """
    Retrieve movie info from IMDB for all movies from today schedule.
    :return: simple confirmation string
    :rtype string
    """

    for tv_type in TV_TYPE:
        movies = result_movies_schedule(tv_type, 'today')  # Retrieve movies from today schedule
        print movies
        for movie in movies:
            print movie
            movie_title = movie['title']
            movie_original_title = movie['originalTitle']
            if movie_original_title is None:
                movie_original_title = movie_title

            try:
                retrieve_movie_from_title(movie_title,
                                          movie_original_title)  # Retrieve movie from IMDB by title and store it
            except ConnectionError:
                print 'ConnectionError, I retry..'
                try:
                    retrieve_movie_from_title(movie_title,
                                              movie_original_title)  # Retrieve movie from IMDB by title and store it
                except Exception:
                    print 'No connection, next one'
                    pass
            except RetrieverError as retriever_error:
                print retriever_error

    return 'OK'
