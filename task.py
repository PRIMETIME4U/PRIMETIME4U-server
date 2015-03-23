import logging
from flask import Flask, request
from werkzeug.exceptions import BadRequest, MethodNotAllowed
from IMDB_retriever import retrieve_movie_from_title
from google.appengine.api import taskqueue
from models import User

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import TV_TYPE, RetrieverError

app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/_ah/start/task/retrieve')
def retrieve():
    """
    Retrieve movie info from IMDB using taskqueue for all movies from "today" schedule.
    :return: simple confirmation string
    :rtype string
    """
    taskqueue.add(url='/_ah/start/task/retrieve/free/tomorrow', method='GET')
    taskqueue.add(url='/_ah/start/task/retrieve/sky/tomorrow', method='GET')
    taskqueue.add(url='/_ah/start/task/retrieve/premium/tomorrow', method='GET')

    return 'OK'


@app.route('/_ah/start/task/suggest')
def suggest():
    """
    :return: simple confirmation string
    :rtype string
    """
    taskqueue.add(url='/_ah/start/task/proposal', method='GET')
    return 'OK'


@app.route('/_ah/start/task/clear')
def clear():
    """
    :return: simple confirmation string
    :rtype string
    """
    taskqueue.add(url='/_ah/start/task/proposal', method='DELETE')
    return 'OK'


@app.route('/_ah/start/task/proposal', methods=['GET', 'DELETE'])
def proposal():
    """
    :return: simple confirmation string
    :rtype string
    """
    if request.method == 'GET':
        users = User.query()
        for user in users:
            taskqueue.add(url='/api/proposal/' + user.key.id(), method='GET')
    elif request.method == 'DELETE':
        users = User.query()
        for user in users:
            user.proposal = None
            user.put()
    else:
        raise MethodNotAllowed
    return 'OK'


@app.route('/_ah/start/task/retrieve/<tv_type>/<day>', methods=['GET'])
def retrieve_type(tv_type, day):
    """
    Retrieve movie info from IMDB for all movies from day schedule by tv type.
    :return: simple confirmation string
    :rtype string
    """

    if tv_type in TV_TYPE:
        movies = result_movies_schedule(tv_type, day)  # Retrieve movies from today schedule
        while len(movies) > 0:
            movie_title = movies[0]['title']
            movie_original_title = movies[0]['originalTitle']
            movie_year = movies[0]['year']
            movie_genre = movies[0]['genres']
            movie_director = movies[0]['director']
            movie_cast = movies[0]['cast']

            if movie_original_title is None:
                movie_original_title = movie_title

            try:
                retrieve_movie_from_title(movie_original_title,
                                          movie_director,
                                          movie_cast,
                                          movie_title,
                                          movies[0]['movieUrl'],
                                          movie_year,
                                          movie_genre)  # Retrieve movie from IMDB(or not) by title and year and store it
                movies.pop(0)
            except Exception as exception:
                logging.error("Error in retrieving %s: %s", movie_original_title, exception)
                if type(exception) is RetrieverError:
                    logging.error("Not our error...")
                    movies.pop(0)
                pass
        return 'OK'
    else:
        raise BadRequest


@app.route('/_ah/start/task/manual/<offset>')
def manual(offset):
    """
    Useful function
    :return: simple confirmation string
    :rtype string
    """
    taskqueue.add(url='/api/manual/' + offset, method='GET')

    return 'OK'