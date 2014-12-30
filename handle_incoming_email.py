
import logging
from flask import Flask
from manage_user import get_current_user
from send_mail import send_feedback
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

app = Flask(__name__)
app.config['DEBUG'] = True
user = get_current_user()

class LogSenderHandler(InboundMailHandler):

    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)
        send_feedback(user)     #mando una mail di ringraziamento del feedback, per provare se funziona la mail ricevuta



