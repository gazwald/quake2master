import logging

from database.orm import Game, Server
from database.functions import get_or_create

from games.shared import Headers, idTechCommon


class Quake2Master(idTechCommon):
    """
    Functions specific to responding to Quake 2 Servers and Clients
    """

    def __init(self):
        super().__init__()

    def get_server(self, address):
        """
        Helper function - simply returns a server based on
        adress:port if it is known
        """
        return self.session.query(Server)\
                           .filter_by(ip=address[0],
                                      port=address[1]).first()

    def process_heartbeat(self, address):
        """
        Processes a server heartbeat (not complete)
        Almost all data sent by a server heartbeat is
        currently discarded in favour of gathering it
        elsewhere
        """
        logging.info(f"Heartbeat from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if not server:
            server = Server(
                active=True,
                ip=address[0],
                port=address[1],
                game=get_or_create(self.session, Game, name='quake2')
            )
            self.session.add(server)

        return None

    def process_shutdown(self, address):
        """
        Sets a server to inactive
        """
        logging.info(f"Shutdown from {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = False

        return None

    def process_ping(self, address):
        """
        Sets server to 'active' and
        Returns a ping acknowledgemnt
        """
        logging.info(f"Sending ack to {address[0]}:{address[1]}")
        server = self.get_server(address)
        if server:
            server.active = True

        return Headers.q2header_ack

    def process_query(self, address):
        """
        Returns a list of servers (as bytes)
        For consumption by clients, eg: qstat
        """
        logging.info(f"Sending servers to {address[0]}:{address[1]}")
        serverstring = [Headers.q2header_servers]
        for server in self.session.query(Server)\
                                  .filter(Server.active)\
                                  .with_entities(Server.ip,
                                                 Server.port).all():
            serverstring.append(self.bytepack(server))

        return b''.join(serverstring)

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