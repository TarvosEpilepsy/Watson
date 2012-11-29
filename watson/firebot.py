from pinder.campfire import Campfire
from twisted.application import service
from twisted.python.failure import DefaultException
import logging, datetime

from watson.chatbot import Chatbot

class Firebot(Chatbot):

    def __init__(self, name, commands, auth_token, subdomain, room_name):
        super(Firebot, self).__init__(name, commands)
        self.auth_token = auth_token
        self.subdomain = subdomain
        self.room_name = room_name
        self.room = None
        self.users = {}

    def speak(self, user, message):
        if not self.room:
            logging.error("Must have a room before I can speak!")
            return

        self.room.speak(message)

    def connect(self):
        self.campfire = Campfire(self.subdomain, self.auth_token)
        self.room = self.campfire.find_room_by_name(self.room_name)
        self.room.join()

        def callback(message):
            text = message['body']
            user_id = message['user_id']
            user = self.users.get(user_id)

            if not user:
                user = self.campfire.user(user_id)['user']['name']
                self.users[user_id] = user

            self.perform_action(user, text)

        def err_callback(exc):
            self.error(exc)

        self.room.join()
        self.room.listen(callback, err_callback, start_reactor=False)
        # self.room.speak(self.welcome_phrase)
        application = service.Application("firebot")
        return application

    def error(self, exc):
        logging.error("Had error at {0}: {1}".format(datetime.datetime.now(), exc))
        if type(exc) == DefaultException:
            self.connect()
        else:
            self.room.leave()

    def disconnect(self):
        logging.error("Got disconnect called")
        # self.room.speak(self.goodbye_phrase)
        self.room.leave()
