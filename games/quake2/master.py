import logging

from database.orm import Game
from database.functions import get_or_create

from games.shared import Headers, Master


class Quake2Master(Master):
    """
    Functions specific to responding to Quake 2 Servers and Clients
    """
    def __init(self):
        super().__init__()
        self.game = get_or_create(self.session, Game, name='quake2')

    def process_request(self, data, address):
        """
        Main point of entry for the class
        All other functions are called from here
        """
        reply = None

        message = data.split(b'\n')
        if message[0].startswith(Headers.q2header_heartbeat):
            reply = self.process_heartbeat(address)
        elif message[0].startswith(Headers.q2header_shutdown):
            reply = self.process_shutdown(address)
        elif message[0].startswith(Headers.q2header_ping):
            reply = self.process_ping(address)
        elif message[0].startswith(Headers.q2query):
            reply = self.process_query(address)
        else:
            logging.warning(f"Unknown message: {message}")

        return reply
