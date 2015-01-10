from google.appengine.ext import ndb
from datetime import date

# TODO: try to use https://cloud.google.com/appengine/docs/python/ndb/modelclass#Model_get_or_insert


class ModelUtils(object):
    @property
    def to_dict(self):
        """
        Property that allow us to print a key-value dict of model.
        :return: model in dict readable form
        :rtype: list of dict
        """
        result = super(ModelUtils, self).to_dict()

        actors = []
        for actor in result['actors']:
            actors.append(actor.get().key.id())  # Get IMDB id of actor instead of entity key
            # actors.append(actor.urlsafe())    # Get urlsafe key
        result['actors'] = actors  # Return a list of IMDB id of actors

        directors = []
        for director in result['directors']:
            directors.append(director.get().key.id())  # Get IMDB id of director instead of entity key
            # directors.append(director.urlsafe())    # Get urlsafe key
        result['directors'] = directors  # Return a list of IMDB id of directors

        writers = []
        for writer in result['writers']:
            writers.append(writer.get().key.id())  # Get IMDB id of writer instead of entity key
            # writers.append(writer.urlsafe())    # Get urlsafe key
        result['writers'] = writers  # Return a list of IMDB id of writers
        return result


class Artist(ModelUtils, ndb.Model):
    """
    Simple artist model.
    The id value is the same id of IMDB.
    When create it remember to declare it:
        Artist(id="id_IMDB", ..)
    """
    name = ndb.StringProperty(required=True)
    photo = ndb.StringProperty()

    @property
    def movies(self):
        """
        Return all movies of an artist.
        :return: all movies in which the artist took part
        :rtype: list of Movie
        """
        return Movie.query().filter(
            Movie.actors == self.key or Movie.writers == self.key or Movie.directors == self.key)


class Movie(ModelUtils, ndb.Model):
    """
    Movie model that follow the description of a film from IMDB site.
    The id value is the same id of IMDB.
    When create it remember to declare it:
        Movie(id="id_IMDB", ..)
    """
    title = ndb.StringProperty()
    original_title = ndb.StringProperty()
    simple_plot = ndb.StringProperty()
    plot = ndb.TextProperty()
    genres = ndb.StringProperty(repeated=True)
    year = ndb.StringProperty()
    run_times = ndb.StringProperty()
    rated = ndb.StringProperty()
    countries = ndb.StringProperty(repeated=True)
    directors = ndb.KeyProperty(Artist, repeated=True)
    writers = ndb.KeyProperty(Artist, repeated=True)
    actors = ndb.KeyProperty(Artist, repeated=True)
    trailer = ndb.StringProperty()
    poster = ndb.StringProperty()
    keywords = ndb.StringProperty(repeated=True)

    def add_actor(self, actor):
        """
        Add actor to movie.
        :param actor: actor to add
        :type actor: Artist
        :return: None
        """
        if actor.key not in self.actors:
            self.actors.append(actor.key)
            self.put()

    def add_director(self, director):
        """
        Add director to movie.
        :param director: director to add
        :type director: Artist
        :return: None
        """
        if director.key not in self.directors:
            self.directors.append(director.key)
            self.put()

    def add_writer(self, writer):
        """
        Add writer to movie.
        :param writer: writer to add
        :type writer: Artist
        :return: None
        """
        if writer.key not in self.writers:
            self.writers.append(writer.key)
            self.put()


class TasteMovie(ModelUtils, ndb.Model):
    """
    This model represents the taste of a user about a movie.
    """
    id_IMDB = ndb.KeyProperty(Movie)
    taste = ndb.IntegerProperty(required=True)

    def add_movie(self, movie):
        """
        Add movie to user's taste.
        :param movie: movie to add
        :type movie: Movie
        :return: None
        """
        self.id_IMDB = movie.key
        self.put()


class TasteArtist(ModelUtils, ndb.Model):
    """
    This model represents the taste of a user about an artist.
    """
    id_IMDB = ndb.KeyProperty(Artist)
    taste = ndb.IntegerProperty(required=True)

    def add_artist(self, artist):
        """
        Add artist to user's taste.
        :param artist: artist to add
        :type artist: Artist
        :return: None
        """
        self.id_IMDB = artist.key
        self.put()


class User(ModelUtils, ndb.Model):
    """
    This model represents a user.
    The id value is the e-mail address of the user.
    When create it remember to declare it:
        User(id="email", ..)
    """
    name = ndb.StringProperty(required=True)
    birth_year = ndb.IntegerProperty()
    gender = ndb.StringProperty(choices=["M", "F"])
    schedule_type = ndb.StringProperty(choices=["free", "mediaset", "sky"], repeated=True)
    watched_movies = ndb.KeyProperty(Movie, repeated=True)
    date_watched = ndb.DateProperty(repeated=True)
    tastes_movies = ndb.KeyProperty(TasteMovie, repeated=True)
    tastes_artists = ndb.KeyProperty(TasteArtist, repeated=True)
    tastes_keywords = ndb.KeyProperty(repeated=True)

    def add_watched_movie(self, movie, date):
        """
        Add movie to watched movies.
        :param movie: movie to add
        :type movie: Movie
        :param date: date the movie been watched
        :type date: date
        :return: None
        """
        self.watched_movies.append(movie.key)
        self.date_watched.append(date)
        self.put()

    def add_taste_movie(self, movie, taste=1):
        """
        Add user's taste of a movie.
        :param movie: movie to be voted
        :type movie: Movie
        :param taste: taste to associate to the movie
        :type taste: integer
        :return: None
        """
        # TODO: improve, I don't know if it is the best way to see if there is yet TasteArtist
        taste_movie = TasteMovie(id=(movie.key.id() + self.key.id()),  # Create the user's taste with unique id
                                 taste=taste)
        taste_movie.add_movie(movie)
        taste_movie_key = taste_movie.put()

        if taste_movie_key not in self.tastes_movies:
            self.tastes_movies.append(taste_movie_key)  # Append the taste to user's tastes
            self.put()

    def add_taste_artist(self, artist, taste=1):
        """
        Add user's taste of an artist.
        :param artist: artist to be voted
        :type artist: Artist
        :param taste: taste to associate to the artist
        :type taste: integer
        :return: None
        """
        # TODO: improve, I don't know if it is the best way to see if there is yet TasteArtist
        taste_artist = TasteArtist(id=(artist.key.id() + self.key.id()),
                                   taste=taste)  # Create the user's taste with unique id
        taste_artist.add_artist(artist)
        taste_artist_key = taste_artist.put()

        if taste_artist_key not in self.tastes_artists:
            self.tastes_artists.append(taste_artist_key)  # Append the taste to user's tastes
            self.put()

    def add_tv_type(self, type):
        """
        Add user's tv type
        :param type: type of tv to be added
        :type type: string representing the type
        :return: None
        """

        if type not in self.schedule_type:
            self.schedule_type.append(type)
            self.put()

    def remove_tv_type(self, type):
        """
        Remove user's tv type from list
        :param type: type of tv to be removed
        :type type: string representing the type to be removed
        :return: None
        """
        if type in self.schedule_type:
            self.schedule_type.remove(type)
            self.put()






