import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from send_mail import forward_mail, send_feedback


class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("Received a message from: " + mail_message.sender)
        content_type, encoded = mail_message.bodies(content_type='text/plain').next()
        body = encoded.decode()
        logging.info(body)

        send_feedback(mail_message.sender)  # Thank the user
        forward_mail(mail_message)  # Forward e-mail to admins


app = webapp.WSGIApplication([LogSenderHandler.mapping()], debug=True)