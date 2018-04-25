import logging

from database.orm import Game
from database.functions import get_or_create

from games.shared import idTechCommon, Master


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
        if message[0].startswith(idTechCommon.headers['quake2']['heartbeat']):
            reply = self.process_heartbeat(address, message[1:])
        elif message[0].startswith(idTechCommon.headers['quake2']['shutdown']):
            reply = self.process_shutdown(address)
        elif message[0].startswith(idTechCommon.headers['quake2']['ping']):
            reply = self.process_ping(address)
        elif message[0].startswith(idTechCommon.headers['quake2']['query']):
            reply = self.process_query(address)
        else:
            logging.warning(f"Unknown message: {message}")

        return reply
