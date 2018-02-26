#!/usr/bin/env python3
import asyncio
import signal
import functools
from sqlalchemy import exc

from database.functions import (create_db_session,
                                create_db_conn)

from masters import Common, Quake2


class MasterServer(Common):
    def connection_made(self, transport):
        self.transport = transport

    def process_stat(self, address):
        self.transport.sendto(b'stat_ack', address)

    def datagram_received(self, data, address):
        reply = None

        if data.startswith(b'stat_ping'):
            reply = self.process_stat(address)
        else:
            reply = q2.process_request(data, address)

        if reply:
            self.transport.sendto(reply, address)

        try:
            session.commit()
        except exc.SQLAlchemyError:
            session.rollback()


def shutdown(signal):
    Common.console_output(f"Caught {signal}, shutting down master server")
    session.close()
    transport.close()
    loop.stop()


if __name__ == '__main__':
    Common.console_output(f"Starting master server")

    engine = create_db_conn()
    session = create_db_session(engine)
    q2 = Quake2(session)

    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                functools.partial(shutdown, signame))

    listen = loop.create_datagram_endpoint(MasterServer,
                                           local_addr=('0.0.0.0', 27900))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    finally:
        loop.close()
