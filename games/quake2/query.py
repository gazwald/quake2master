import socket
import re
import logging
from datetime import datetime
from multiprocessing import Pool

from database.orm import (Server,
                          Player,
                          State)

from games import idTechCommon


class Quake2Query(idTechCommon):
    def __init__(self):
        super().__init__()
        self.update_state()

    def update_state(self):
        self.state = self.session.query(State).filter(State.id == 1).first()
        if not self.state:
            self.state = State()

        if not self.state.running:
            logging.info(f"Starting to query servers")
            self.state.running = True
            self.state.started = datetime.now()
            self.session.add(self.state)
            self.session.commit()
            self.query_servers()
        else:
            logging.info(f"Already running")
            self.shutdown()

    def update_active_server(self, server):
        logging.info(f"Marking {server.ip}:{server.port} active")
        server.country = self.get_country(server.ip)
        server.active = True
        self.session.add(server)

    def update_inactive_server(self, server):
        logging.info(f"Marking {server.ip}:{server.port} inactive")
        server.active = False
        self.session.add(server)

    def update_players(self, server, players):
        """
        This is dumb, fix it.
        """
        player_regex = re.compile('(?P<score>-?\d+) (?P<ping>\d+) (?P<name>".+")', flags=re.ASCII)
        player_list = []
        self.session.query(Player).filter(Player.server == server).delete()
        self.session.commit()
        for playerstate in players:
            if playerstate:
                playerstate = playerstate.decode('ascii')
                playerstate = re.match(player_regex, playerstate)
                player_list.append(Player(
                    score=int(playerstate.group('score')),
                    ping=int(playerstate.group('ping')),
                    name=playerstate.group('name'),
                    server=server
                ))
        self.session.add_all(player_list)

    def process_server_info(self, server, data):
        message = data.split(b'\n')
        if message[0].startswith(idTechCommon['quake2']['print']):
            logging.info(f"Updating server info for {server}")
            status = message[1]
            players = message[2:]
            if players:
                self.update_players(server, players)

            if status:
                self.update_status(server, self.dictify(status))

    def connect_to_server(self, server):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(5)
            try:
                logging.info(f"Connecting to {server}...")
                s.connect((server.ip, server.port))
                s.send(idTechCommon['quake2']['query'])
                data = s.recv(1024)
            except socket.error as err:
                logging.debug(f"Connection error: {err}")
                self.update_inactive_server(server)
            else:
                self.update_active_server(server)
                self.process_server_info(server, data)
            finally:
                self.session.commit()

    def query_servers(self):
        with Pool(10) as pool:
            pool.map(self.connect_to_server,
                     self.session.query(Server).filter(Server.active))

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def shutdown(self, signum, frame):
        if signum:
            logging.info(f"Caught {signum}, shutting down")
        else:
            logging.info(f"Finished querying servers")

        self.state.ended = datetime.now()
        self.state.running = False
        self.session.add(self.state)
        self.session.commit()
        self.session.close()
