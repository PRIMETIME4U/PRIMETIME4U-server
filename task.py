import json
from flask import Flask
from models import User, Movie

from movie_selector import random_movie_selection
from send_mail import send_suggestion
from tv_scheduling import result_movies_schedule
from utilities import get

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/task/suggest/')
def random_suggest():
    """
    Send a random movie suggest for all users.
    :return: simple confirmation string
    :rtype string
    """
    users = User.query()  # Get all users

    for user in users.iter():
        send_suggestion(user, random_movie_selection(result_movies_schedule("free", "today")))  # Send suggest for user

    return "Suggestions sended"





@app.route('/task/retrieve/')
def retrieve():
    movies = result_movies_schedule("free", "today")
    for movie in movies:
        movie_title = movie['originalTitle'].encode('utf-8') if movie['originalTitle'] is not None else movie[
            'title'].encode('utf-8')
        print movie_title
        url = 'http://www.myapifilms.com/imdb?title=' + movie_title + '&format=JSON&aka=0&business=0&seasons=0&seasonYear=0&technical=0&filter=N&exactFilter=0&limit=1&lang=en-us&actors=N&biography=0&trailer=1&uniqueName=0&filmography=0&bornDied=0&starSign=0&actorActress=0&actorTrivia=0&movieTrivia=0&awards=0'
        page_json = get(url).encode('utf-8')
        json_data = json.loads(page_json)
        obj = Movie(id=json_data[0]["idIMDB"],original_title=json_data[0]["originalTitle"],plot=json_data[0]["plot"],poster=json_data[0]["urlPoster"],rated=json_data[0]["rated"],run_times=json_data[0]["runtime"][0],title=json_data[0]["title"],simple_plot=json_data[0]["simplePlot"])

        obj.put()

    return 'aggiunto'