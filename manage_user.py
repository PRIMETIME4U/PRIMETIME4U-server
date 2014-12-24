from google.appengine.api import users
from google.appengine.api.users import UserNotFoundError
from models import User as modelUser


class User(users.User):
    """
    Class inherit from users.User in order to add some useful methods.
    """

    def subscribe(self):
        """
        Add user in the datastore.
        :return None
        """
        user = modelUser(id=self.email(),
                         name=self.nickname())

        user.put()

    def unsubscribe(self):
        """
        Delete user from the datastore.
        :return None
        """
        user = modelUser.get_by_id(self.email())
        user.key.delete()

    def is_subscribed(self):
        """
        Check if user is already subscribed (and then in the datastore).
        :return true if user is subscribed, false otherwise
        :rtype Boolean
        """
        user = modelUser.get_by_id(self.email())
        print user

        return True if user is not None else False


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