from flask import Flask, jsonify, redirect

from werkzeug.exceptions import default_exceptions, HTTPException
from google.appengine.api import users
from manage_user import get_current_user
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

            return 'Welcome, %s! (<a href="%s">sign out</a>) \n ' \
                   '(<a href="%s">Unsubscribe!</a>)' \
                   % (user.nickname(), users.create_logout_url('/'), "/unsubscribe")
        else:

            return 'Welcome, %s! (<a href="%s">sign out</a>) \n ' \
                   '(<a href="%s">Subscribe!</a>)' \
                   % (user.nickname(), users.create_logout_url('/'), "/subscribe")
    else:
        return redirect(users.create_login_url())


@app.route('/subscribe')
def subscribe():
    """
    View that allow to subscribe current user.
    :return: None, redirect to home
    """
    user = get_current_user()

    if user:
        user.subscribe()

    return redirect('/')


@app.route('/unsubscribe')
def unsubscribe():
    """
    View that allow to unsubscribe current user.
    :return: None, redirect to home
    """
    user = get_current_user()

    if user:
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
