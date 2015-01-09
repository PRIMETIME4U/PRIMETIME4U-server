from flask import Flask, jsonify, redirect, request

from werkzeug.exceptions import default_exceptions, HTTPException, NotFound, abort, BadRequest, MethodNotAllowed
from google.appengine.api import users
from manage_user import get_current_user
from models import User, Artist, Movie, TasteArtist, TasteMovie
from send_mail import confirm_subscription, confirm_unsubscription
from tv_scheduling import result_movies_schedule

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


__all__ = ["json_api"]


def json_api(import_name, **kwargs):
    """
    Creates a JSON-oriented Flask app.

    All error responses that you don't specifically
    manage yourself will have applications/json content
    type, and will contain JSON like this (just an example)

    {
        "code": 1,
        "errorMessage": "The requested URL was not found on the server.  If you entered the URL manually please [...] ",
        "errorType": "404: Not Found"
    }

    More here: http://flask.pocoo.org/snippets/83/ (ad-hoc by pincopallino93)
    """

    def make_json_error(ex):
        response = jsonify(errorMessage=str(ex.description) if hasattr(ex, 'description') else str(ex), code=1,
                           errorType=str(ex))
        response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)

        return response

    app = Flask(import_name, **kwargs)

    for code in default_exceptions:
        app.error_handler_spec[None][code] = make_json_error

    return app


app = json_api(__name__)

# TODO: manage exception as maintenance for all call


@app.route('/')
def hello():
    """
    Main view with login page and links for subscription and sign out.
    :return: HTML page or None (with redirection to home)
    """
    user = get_current_user()

    if user:

        if user.is_subscribed():

            return 'Welcome, {}! (<a href="{}">sign out</a>) <br>' \
                   '<a href="{}">Unsubscribe!</a>' \
                .format(user.nickname(), users.create_logout_url('/'), "/unsubscribe")
        else:

            return 'Welcome, {}! (<a href="{}">sign out</a>) <br>' \
                   '<a href="{}">Subscribe!</a>' \
                .format(user.nickname(), users.create_logout_url('/'), "/subscribe")
    else:
        return 'PRIMETIME4U, The only app that allows you to plop down to the couch and simply enjoy a movie <br>' \
               '<a href="{}">Sign in</a>'.format(users.create_login_url())


@app.route('/subscribe')
def subscribe():
    """
    View that allow to subscribe current user.
    :return: None, redirect to home
    """
    user = get_current_user()

    if user:
        user.subscribe()
        confirm_subscription(user.get_ndb_user())  # Send confirmation mail

    return redirect('/')


@app.route('/unsubscribe')
def unsubscribe():
    """
    View that allow to unsubscribe current user.
    :return: None, redirect to home
    """
    user = get_current_user()

    if user:
        confirm_unsubscription(user.get_ndb_user())  # Send confirmation mail
        user.unsubscribe()

    return redirect('/')


@app.route('/schedule/<tv_type>/<day>')
def schedule(tv_type, day):
    """
    Returns a JSON containing the TV programming of <tv_type> in the <day>.
    :param tv_type: type of TV from get schedule, possible value (free, sky, premium)
    :type tv_type: string
    :param day: interested day, possible value (today, tomorrow, future)
    :type day: string
    :return: schedule
        {"code": 0, "data": { "day": day, "schedule": [{"channel": channel_name, "originalTitle": original_title,
        "time": time, "title": title}, .. ], "type": tv_type}}
    :rtype: JSON
    """
    return jsonify(code=0, data={"type": tv_type, "day": day, "schedule": result_movies_schedule(tv_type, day)})


@app.route('/tastes/<user_id>/<type>', methods=['GET', 'POST'])
def tastes(user_id, type):
    user = User.get_by_id(user_id)

    if request.method == 'POST':
        if type == 'artist':
            artist_name = request.form['artist_name']

            artist = Artist.query(Artist.name == artist_name).get()
            if artist is not None:
                user.add_taste_artist(artist)
            return get_tastes_artists_list(user, type)
        elif type == 'movie':
            movie_original_title = request.form['movie_title']

            movie = Movie.query(Movie.original_title == movie_original_title).get()
            if movie is not None:
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

# @app.route('/addartist')
# def addartist():
#     obj = Artist(id='nm0004695',
#                  name='Jessica Alba',
#                  photo='http://ia.media-imdb.com/images/M/MV5BODYxNzE4OTk5Nl5BMl5BanBnXkFtZTcwODYyMDYzMw@@._V1_SY98_CR3,0,67,98_AL_.jpg')
#     obj.put()
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


def get_tastes_artists_list(user, type):
    """

    :param user:
    :type user:
    :param type:
    :type type:
    :return:
    :rtype:
    """
    tastes_artists_id = user.tastes_artists

    artists = []

    for taste_artist_id in tastes_artists_id:
        taste_artist = TasteArtist.get_by_id(taste_artist_id.id())
        artist_id = taste_artist.id_IMDB.id()
        artist = Artist.get_by_id(artist_id)
        artists.append({"id_IMDB": artist_id, "name": artist.name, "photo": artist.photo})

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