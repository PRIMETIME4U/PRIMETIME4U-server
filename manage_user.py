from google.appengine.api import users
from google.appengine.api.users import UserNotFoundError
from models import User as modelUser


class User(users.User):
    """
    Class inherit from users.User in order to add some useful methods.
    """

    def subscribe(self, name=None, birth_year=None, gender=None, gcm_key=None):
        """
        Add user in the datastore.
        :param name: name of the user
        :type name: string
        :param birth_year: birth year of the user
        :type birth_year: string
        :param gender: gender of the user
        :type gender: string
        :return None
        """
        user = modelUser(id=self.email(),
                         name=self.nickname())

        if name is not None:
            user.name = name
        if birth_year is not None:
            user.birth_year = int(birth_year)
        if gender is not None:
            user.gender = gender.upper()

        if gcm_key is not None:
            user.gcm_key = gcm_key

        user.put()

    def unsubscribe(self):
        """
        Delete user from the datastore.
        :return None
        """
        user = self.get_ndb_user()
        user.key.delete()

    def is_subscribed(self):
        """
        Check if user is already subscribed (and then in the datastore).
        :return true if user is subscribed, false otherwise
        :rtype Boolean
        """
        user = self.get_ndb_user()

        return True if user is not None else False

    def get_ndb_user(self):
        """
        Get user from the datastore.
        :return user from the datastore
        :rtype models.User
        """
        return modelUser.get_by_id(self.email())


def get_current_user():
    """
    Retrieve current user.
    :return: return current user or None in case of user not found
    :rtype User or None
    """
    try:
        return User()
    except UserNotFoundError:
        return None

'''
# TODO: finish next parts
def sort_user_tastes(user_id):
    """
    It order all the tastes, one type at time, the artists, the movies and the genres.
    :param user_id: user id who to order tastes
    :return: None
    """

    user = modelUser.get_by_id(user_id)

    #sort_movies_tastes(user)
    #sort_artists_tastes(user)
    #sort_genres_tastes(user)


def sort_movies_tastes(user):

    movie_tastes = user.tastes_movies


def sort_artists_tastes(user):

    artists_tastes = user.tastes_artists
'''
