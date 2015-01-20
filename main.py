from flask import redirect

from google.appengine.api import users
from manage_user import get_current_user
from send_mail import confirm_subscription, confirm_unsubscription
from utilities import json_api

app = json_api(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


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