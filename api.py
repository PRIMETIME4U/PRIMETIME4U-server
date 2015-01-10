from flask import jsonify, request

from werkzeug.exceptions import BadRequest, MethodNotAllowed, InternalServerError
from IMDB_retriever import retrieve_movie
from main import json_api
from manage_user import User
from models import Artist, Movie, TasteArtist, TasteMovie
from models import User as modelUser
from utilities import RetrieverError

app = json_api(__name__)
app.config['DEBUG'] = True


@app.route('/api/tastes/<user_id>/<type>', methods=['GET', 'POST'])
def tastes(user_id, type):
    """

    :param user_id:
    :param type:
    :return:
    """
    user = modelUser.get_by_id(user_id)

    if user is not None:
        if request.method == 'POST':
            if type == 'artist':
                artist_name = request.form['artist_name']

                artist = Artist.query(Artist.name == artist_name).get()
                if artist is not None:
                    user.add_taste_artist(artist)
                # else:
                # retrieve_artist
                return get_tastes_artists_list(user, type)
            elif type == 'movie':
                movie_original_title = request.form['movie_title']

                movie = Movie.query(Movie.original_title == movie_original_title).get()
                if movie is None:
                    try:
                        movie_key = retrieve_movie(movie_original_title)  # Retrieve if is not in the datastore
                    except RetrieverError as retriever_error:
                        raise InternalServerError(retriever_error)
                    movie = Movie.get_by_id(movie_key.id())

                user.add_taste_movie(movie)
                return get_tastes_movies_list(user, type)
            else:
                raise BadRequest
        elif request.method == 'GET':
            if type == 'artist':
                return get_tastes_artists_list(user, type)
            elif type == 'movie':
                return get_tastes_movies_list(user, type)
            else:
                raise BadRequest
        else:
            raise MethodNotAllowed
    else:
        raise InternalServerError(user_id + ' is not subscribed')


@app.route('/api/subscribe/', methods=['POST'])
def subscribe():
    """
    Subscribe user from App.
    :return:
    """
    if request.method == 'POST':

        json_data = request.get_json()
        user_id = json_data['user_id']

        user = User(email=user_id)

        if user.is_subscribed():
            raise InternalServerError(user_id + ' is already subscribed')
        else:
            user.subscribe(name=json_data['user_name'], birth_year=json_data['user_birth_year'],
                           gender=json_data['user_gender'])
            return jsonify(code=0, data={"user_id": user_id, "message": "User subscribed successful!"})
    else:
        raise MethodNotAllowed


@app.route('/api/unsubscribe/', methods=['POST'])
def unsubscribe():
    """
    Unsubscribe user from App.
    :return:
    """
    if request.method == 'POST':
        user_id = request.form['user_id']

        user = User(email=user_id)

        if not user.is_subscribed():
            raise InternalServerError(user_id + ' is not subscribed')
        else:
            user.unsubscribe()
            return jsonify(code=0, data={"user_id": user_id, "message": "User unsubscribed successful!"})
    else:
        raise MethodNotAllowed


# @app.route('/addartist')
# def addartist():
# obj = Artist(id='nm0004695',
# name='Jessica Alba',
# photo='http://ia.media-imdb.com/images/M/MV5BODYxNzE4OTk5Nl5BMl5BanBnXkFtZTcwODYyMDYzMw@@._V1_SY98_CR3,0,67,98_AL_.jpg')
# obj.put()
#
#     return 'Aggiunta Jessica Alba'
#
#
# @app.route('/addmovie')
# def addmovie():
#     obj = Movie(id='tt0120667',
#                 original_title='Fantastic Four')
#     actor = Artist.get_by_id('nm0004695')
#     movie_id = obj.put().id()
#     movie = Movie.get_by_id(movie_id)
#     movie.add_actor(actor)
#
#     return 'Aggiunto Fantastic Four'


# TODO: complete docstring
def get_tastes_artists_list(user, type):
    """

    :param user:
    :type user:
    :param type:
    :type type:
    :return:
    :rtype:
    """
    tastes_artists_id = user.tastes_artists  # Get all taste_artists' keys

    artists = []

    for taste_artist_id in tastes_artists_id:  # For all key get artist's info an
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())
        artist_id = taste_artist.id_IMDB.id()
        artist = Artist.get_by_id(artist_id)  # Get artist
        artists.append({"id_IMDB": artist_id, "name": artist.name, "photo": artist.photo}) # Append Arti

    return jsonify(code=0, data={"user_id": user.key.id(), "type": type, "tastes": artists})


def get_tastes_movies_list(user, type):
    """

    :param user:
    :type user:
    :param type:
    :type type:
    :return:
    :rtype:
    """
    tastes_movies_id = user.tastes_movies

    movies = []

    for taste_movie_id in tastes_movies_id:
        taste_movie = TasteMovie.get_by_id(taste_movie_id.id())
        movie_id = taste_movie.id_IMDB.id()
        movie = Movie.get_by_id(movie_id)
        movies.append({"id_IMDB": movie_id, "original_title": movie.original_title, "poster": movie.poster})

    return jsonify(code=0, data={"user_id": user.key.id(), "type": type, "tastes": movies})