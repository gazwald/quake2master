#!/usr/bin/env python3
import asyncio
import signal
import functools
import logging
import configparser
import os
import sys
from sqlalchemy import exc

from database.functions import (create_db_session,
                                create_db_conn)

from games.shared import idTechCommon
from games import Quake2Master


class MasterServer():
    def connection_made(self, transport):
        self.transport = transport

    def process_stat(self, address):
        self.transport.sendto(b'stat_ack', address)

    def datagram_received(self, data, address):
        reply = None

        if data.startswith(b'stat_ping'):
            reply = self.process_stat(address)
        elif idTechCommon.is_q2(data):
            reply = Q2.process_request(data, address)

        if reply:
            self.transport.sendto(reply, address)

        try:
            SESSION.commit()
        except exc.SQLAlchemyError:
            SESSION.rollback()


def shutdown(sig):
    logging.info(f"Caught {sig}, shutting down master server")
    SESSION.close()
    TRANSPORT.close()
    LOOP.stop()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'config.ini'))

    logging.basicConfig(stream=sys.stdout,
                        level=getattr(logging, str.upper(config['logging'].get('level', 'INFO'))),
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logging.info(f"Starting master server")

    ENGINE = create_db_conn(config['general'].get('environment', 'production'))
    SESSION = create_db_session(ENGINE)
    Q2 = Quake2Master(SESSION)

    LOOP = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        LOOP.add_signal_handler(getattr(signal, signame),
                                functools.partial(shutdown, signame))

    BIND = (config['general'].get('address', '0.0.0.0'),
            config['general'].get('port', 27900))

    LISTEN = LOOP.create_datagram_endpoint(MasterServer,
                                           local_addr=BIND)
    TRANSPORT, PROTOCOL = LOOP.run_until_complete(LISTEN)

    try:
        LOOP.run_forever()
    finally:
        LOOP.close()
