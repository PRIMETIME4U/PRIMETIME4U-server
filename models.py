from google.appengine.ext import ndb


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
            directors.append(director.get().key.id())  # Get IMDB id of actor instead of entity key
            # directors.append(director.urlsafe())    # Get urlsafe key
        result['directors'] = directors  # Return a list of IMDB id of directors

        writers = []
        for writer in result['writers']:
            writers.append(writer.get().key.id())  # Get IMDB id of actor instead of entity key
            # writers.append(writer.urlsafe())    # Get urlsafe key
        result['writers'] = writers  # Return a list of IMDB id of writers
        return result


class Artist(ModelUtils, ndb.Model):
    """
    Simple artist model.
    The id value is the same id of IMDB.
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
    """
    title = ndb.StringProperty()
    original_title = ndb.StringProperty()
    simple_plot = ndb.StringProperty()
    plot = ndb.TextProperty()
    genres = ndb.StringProperty(repeated=True)
    year = ndb.IntegerProperty()
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
        self.actors.append(actor.key)
        self.put()

    def add_director(self, director):
        """
        Add director to movie.
        :param director: director to add
        :type director: Artist
        :return: None
        """
        self.directors.append(director.key)
        self.put()

    def add_writer(self, writer):
        """
        Add writer to movie.
        :param writer: writer to add
        :type writer: Artist
        :return: None
        """
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
    """
    name = ndb.StringProperty(required=True)
    birth_year = ndb.IntegerProperty()
    gender = ndb.StringProperty(choices=["M", "F"])
    watched_movies = ndb.KeyProperty(Movie, repeated=True)
    tastes_movies = ndb.KeyProperty(TasteMovie, repeated=True)
    tastes_artists = ndb.KeyProperty(TasteArtist, repeated=True)
    tastes_keywords = ndb.KeyProperty(repeated=True)

    def add_watched_movie(self, movie):
        """
        Add movie to watched movies.
        :param movie: movie to add
        :type movie: Movie
        :return: None
        """
        self.watched_movies.append(movie.key)
        self.put()

    def add_taste_movie(self, movie, taste):
        """
        Add user's taste of a movie.
        :param movie: movie to be voted
        :type movie: Movie
        :param taste: taste to associate to the movie
        :type taste: integer
        :return: None
        """
        taste_movie = TasteMovie(id=(movie.key.id() + self.key.id()),   # Create the user's taste with unique id
                                 taste=taste)
        taste_movie.add_movie(movie)
        taste_movie_key = taste_movie.put()

        self.tastes_movies.append(taste_movie_key)  # Append the taste to user's tastes
        self.put()

    def add_taste_artist(self, artist, taste):
        """
        Add user's taste of an artist.
        :param artist: artist to be voted
        :type artist: Artist
        :param taste: taste to associate to the artist
        :type taste: integer
        :return: None
        """
        taste_artist = TasteArtist(id=(artist.key.id() + self.key.id()),
                                   taste=taste)  # Create the user's taste with unique id
        taste_artist.add_artist(artist)
        taste_artist_key = taste_artist.put()

        self.tastes_artists.append(taste_artist_key)    # Append the taste to user's tastes
        self.put()