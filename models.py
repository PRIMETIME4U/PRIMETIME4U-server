from google.appengine.ext import ndb
from datetime import date

from utilities import TV_TYPE, GENRES


class ModelUtils(object):
    @property
    def to_dict(self):
        """
        Property that allow us to print a key-value dict of model.
        :return: model in dict readable form
        :rtype: list of dict
        """
        result = super(ModelUtils, self).to_dict()

        if type(self) is Movie:

            result['genres'] = " | ".join(result['genres'])

            actors = []
            for actor in result['actors']:
                actor = Artist.get_by_id(actor.get().key.id())
                actors.append(actor.to_dict)
            result['actors'] = actors  # Return a list of actors' name

            directors = []
            for director in result['directors']:
                director = Artist.get_by_id(director.get().key.id())
                directors.append(director.to_dict)
            result['directors'] = directors  # Return a list of directors' name

            writers = []
            for writer in result['writers']:
                writer = Artist.get_by_id(writer.get().key.id())
                writers.append(writer.to_dict)
            result['writers'] = writers  # Return a list of writers' name
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
    plot_it = ndb.TextProperty()
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
    movie = ndb.KeyProperty(Movie)
    taste = ndb.FloatProperty(required=True)

    def add_movie(self, movie):
        """
        Add movie to user's taste.
        :param movie: movie to add
        :type movie: Movie
        :return: None
        """
        self.movie = movie.key
        self.put()

    def update_taste(self, taste):
        self.taste += taste
        self.put()


class TasteArtist(ModelUtils, ndb.Model):
    """
    This model represents the taste of a user about an artist.
    """
    artist = ndb.KeyProperty(Artist)
    taste = ndb.FloatProperty(required=True)

    def add_artist(self, artist):
        """
        Add artist to user's taste.
        :param artist: artist to add
        :type artist: Artist
        :return: None
        """
        self.artist = artist.key
        self.put()

    def update_taste(self, taste):
        self.taste += taste
        self.put()


class TasteGenre(ModelUtils, ndb.Model):
    """
    This model represents the taste of a user about a genre.
    """
    genre = ndb.StringProperty(choices=GENRES)
    taste = ndb.FloatProperty(required=True)

    def update_taste(self, taste):
        self.taste += taste
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
    tv_type = ndb.StringProperty(choices=TV_TYPE, repeated=True)
    watched_movies = ndb.KeyProperty(Movie, repeated=True)
    date_watched = ndb.DateProperty(repeated=True)
    tastes_movies = ndb.KeyProperty(TasteMovie, repeated=True)
    tastes_artists = ndb.KeyProperty(TasteArtist, repeated=True)
    tastes_genres = ndb.KeyProperty(TasteGenre, repeated=True)
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
        if movie.key not in self.watched_movies:
            self.watched_movies.append(movie.key)
            self.date_watched.append(date)
            self.put()

    def add_taste_movie(self, movie, taste=1.0):
        """
        Add user's taste of a movie.
        :param movie: movie to be voted
        :type movie: Movie
        :param taste: taste to associate to the movie
        :type taste: float
        :return: None
        """
        # TODO: improve, I don't know if it is the best way to see if there is yet TasteArtist
        taste_movie = TasteMovie(id=(movie.key.id() + self.key.id()),  # Create the user's taste with unique id
                                 taste=taste)
        taste_movie.add_movie(movie)
        taste_movie_key = taste_movie.put()

        movie = Movie.get_by_id(movie.key.id())
        for actor in movie.actors:
            artist = Artist.get_by_id(actor.id())
            self.add_taste_artist(artist, 0.2)

        for director in movie.directors:
            artist = Artist.get_by_id(director.id())
            self.add_taste_artist(artist, 0.2)

        for writer in movie.writers:
            artist = Artist.get_by_id(writer.id())
            self.add_taste_artist(artist, 0.2)

        for genre in movie.genres:
            self.add_taste_genre(genre, 0.2)

        if taste_movie_key not in self.tastes_movies:
            self.tastes_movies.append(taste_movie_key)  # Append the taste to user's tastes
            self.put()

    def add_taste_artist(self, artist, taste=1.0):
        """
        Add user's taste of an artist.
        :param artist: artist to be voted
        :type artist: Artist
        :param taste: taste to associate to the artist
        :type taste: float
        :return: None
        """
        taste_artist = TasteArtist.get_by_id(artist.key.id() + self.key.id())
        if taste_artist is None:
            taste_artist = TasteArtist(id=(artist.key.id() + self.key.id()),
                                       taste=taste)  # Create the user's taste with unique id
            taste_artist.add_artist(artist)
            taste_artist_key = taste_artist.put()

            if taste_artist_key not in self.tastes_artists:
                self.tastes_artists.append(taste_artist_key)  # Append the taste to user's tastes
                self.put()
        else:
            if taste == 1 and taste_artist.taste > 1:
                pass
            else:
                taste_artist.update_taste(taste)

    def add_taste_genre(self, genre, taste=1.0):
        if genre in GENRES:
            taste_genre = TasteGenre.get_by_id(genre + self.key.id())
            if taste_genre is None:
                taste_genre = TasteGenre(id=(genre + self.key.id()),
                                         genre=genre,
                                         taste=taste)
                taste_genre_key = taste_genre.put()

                if taste_genre_key not in self.tastes_genres:
                    self.tastes_genres.append(taste_genre_key)
                    self.put()
            else:
                if taste == 1 and taste_genre.taste > 1:
                    pass
                else:
                    taste_genre.update_taste(taste)

    def remove_taste_movie(self, movie):
        """

        :param movie:
        :return:
        """
        taste_movie_id = movie.key.id() + self.key.id()
        taste_movie = TasteMovie.get_by_id(taste_movie_id)

        if taste_movie is not None:
            taste_movie_key = taste_movie.key

            movie = Movie.get_by_id(movie.key.id())
            for actor in movie.actors:
                artist = Artist.get_by_id(actor.id())
                taste_artist = TasteArtist.get_by_id(actor.id() + self.key.id())

                if taste_artist is not None:
                    taste_artist.update_taste(-0.2)
                else:
                    self.add_taste_artist(artist, -0.2)

                if taste_artist.taste == 0:
                    self.remove_taste_artist(artist)

            for director in movie.directors:
                artist = Artist.get_by_id(director.id())
                taste_artist = TasteArtist.get_by_id(director.id() + self.key.id())

                if taste_artist is not None:
                    taste_artist.update_taste(-0.2)
                else:
                    self.add_taste_artist(artist, -0.2)

                if taste_artist.taste == 0:
                    self.remove_taste_artist(artist)

            for writer in movie.writers:
                artist = Artist.get_by_id(writer.id())
                taste_artist = TasteArtist.get_by_id(writer.id() + self.key.id())

                if taste_artist is not None:
                    taste_artist.update_taste(-0.2)
                else:
                    self.add_taste_artist(artist, -0.2)

                if taste_artist.taste == 0:
                    self.remove_taste_artist(artist)

            for genre in movie.genres:
                taste_genre = TasteGenre.get_by_id(genre + self.key.id())

                if taste_genre is not None:
                    taste_genre.update_taste(-0.2)
                else:
                    self.add_taste_genre(genre, -0.2)

                if taste_genre.taste == 0:
                    self.remove_taste_genre(genre)

            taste_movie.key.delete()
            if taste_movie_key in self.tastes_movies:
                self.tastes_movies.remove(taste_movie_key)
                self.put()

    def remove_taste_artist(self, artist):
        """

        :param artist:
        :return:
        """
        taste_artist_id = artist.key.id() + self.key.id()
        taste_artist = TasteArtist.get_by_id(taste_artist_id)
        if taste_artist.taste == 1 or taste_artist.taste == 0:
            taste_artist_key = taste_artist.key

            taste_artist.key.delete()
            if taste_artist_key in self.tastes_artists:
                self.tastes_artists.remove(taste_artist_key)
                self.put()
        elif taste_artist.taste > 1:
            taste_artist.update_taste(-1)

    def remove_taste_genre(self, genre):
        taste_genre_id = genre + self.key.id()
        taste_genre = TasteGenre.get_by_id(taste_genre_id)
        if taste_genre.taste == 1 or taste_genre.taste == 0:
            taste_genre_key = taste_genre.key

            taste_genre.key.delete()
            if taste_genre_key in self.tastes_genres:
                self.tastes_genres.remove(taste_genre_key)
                self.put()
        elif taste_genre.taste > 1:
            taste_genre.update_taste(-1)

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






