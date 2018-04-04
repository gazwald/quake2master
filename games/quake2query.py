import socket
import GeoIP
import re
import logging
from datetime import datetime

from database.orm import (Server,
                          Status,
                          Map,
                          Version,
                          Gamename,
                          Player,
                          State,
                          Country)

from database.functions import get_or_create

from games import Headers


class Quake2Query():
    def __init__(self, session):
        self.gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

        self.session = session
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
        server.country = get_or_create(self.session,
                                       Country,
                                       name_short=self.gi.country_code_by_addr(server.ip),
                                       name_long=self.gi.country_name_by_addr(server.ip))
        server.active = True
        self.session.add(server)

    def update_inactive_server(self, server):
        logging.info(f"Marking {server.ip}:{server.port} inactive")
        server.active = False
        self.session.add(server)

    def dictify(message):
        """
        Input:
            b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\fraglimit\\0'
        Split the above byte-string into list of strings resulting in:
            ['cheats', '0', 'deathmatch', '1', 'dmflags', '16', 'fraglimit', '0']
        Zip the above list of byte strings and then convert zip object into a dict:
            {'cheats': '0', 'deathmatch': '1', 'dmflags': '16', 'fraglimit': '0']
        For each key/value try to convert it to an int ahead of time.
        TODO: Look for improvements here
        """
        strmessage = message.decode('ascii')
        strstatus = strmessage.split('\\')[1:]
        zipped = zip(strstatus[0::2], strstatus[1::2])
        status = dict((x, y) for x, y in zipped)

        for k, v in status.items():
            try:
                status[k] = int(v)
            except ValueError:
                pass

        return status

    def update_status(self, server, serverstatus):
        serverstatus['server'] = server
        serverstatus['version'] = get_or_create(self.session,
                                                Version,
                                                name=serverstatus.get('version'))

        serverstatus['mapname'] = get_or_create(self.session,
                                                Map,
                                                name=serverstatus.get('mapname'))

        serverstatus['gamename'] = get_or_create(self.session,
                                                 Gamename,
                                                 name=serverstatus.get('gamedir', 'baseq2'))

        serverstatus['clients'] = self.session.query(Player).join(Player.server).filter(Player.server == server).count()

        status = self.session.query(Status).join(Status.server).filter(Status.server == server).first()

        if status:
            for k, v in serverstatus:
                setattr(status, k, v)
        else:
            status = Status(**serverstatus)

        self.session.add(status)

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
        if message[0].startswith(Headers.q2header_print):
            logging.info(f"Updating server info for {server}")
            status = message[1]
            players = message[2:]
            if players:
                self.update_players(server, players)

            if status:
                self.update_status(server, self.dictify(status))

    def query_servers(self):
        # TODO: Replce with asyncio
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(5)
            for server in self.session.query(Server).filter(Server.active):
                try:
                    logging.info(f"Connecting to {server}...")
                    s.connect((server.ip, server.port))
                    s.send(Headers.q2header_query)
                    data = s.recv(1024)
                except socket.error as err:
                    logging.debug(f"Connection error: {err}")
                    self.update_inactive_server(server)
                    continue
                else:
                    self.update_active_server(server)
                    self.process_server_info(server, data)
                finally:
                    self.session.commit()

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
