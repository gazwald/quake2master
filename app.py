#!/usr/bin/env python3
import asyncio
from datetime import datetime

from database.functions import (create_db_session,
                                create_db_conn)

from masters import Quake2


class MasterServer:
    def __init__(self):
        self.header = b'\xff\xff\xff\xff'
        self.header_ack = b''.join([self.header, b'ack'])
        self.header_stat = b''.join([self.header, b'stat'])
        self.header_servers = b''.join([self.header, b'servers '])

    @staticmethod
    def console_output(message):
        print(f"{datetime.utcnow().isoformat()}: {message}")

    def connection_made(self, transport):
        self.transport = transport

    def process_stat(self, address):
        self.transport.sendto(self.header_ack, address)

    def datagram_received(self, data, address):
        reply = None
        message = data.split(b'\n')
        if message[0].startswith(self.header_stat):
            reply = self.process_stat(address)
        elif message[0].startswith(self.header):
            command = message[0][4:]
            if command.startswith(b"heartbeat"):
                self.console_output(f"Heartbeat from {address[0]}:{address[1]}")
                q2.process_heartbeat(address)
            elif command.startswith(b"shutdown"):
                self.console_output(f"Shutdown from {address[0]}:{address[1]}")
                q2.process_shutdown(address)
            elif command.startswith(b"ping"):
                self.console_output(f"Sending ack to {address[0]}:{address[1]}")
                reply = q2.process_ping(address)
            else:
                self.console_output(f"Unknown command: {command}")
        elif message[0].startswith(b"query"):
            self.console_output(f"Sending servers to {address[0]}:{address[1]}")
            reply = q2.process_query(address)
        else:
            self.console_output(f"Unable to process message")

        if reply:
            self.transport.sendto(reply, address)

        try:
            session.commit()
        except:
            session.rollback()


if __name__ == '__main__':
    """
    asyncio magic
    """
    engine = create_db_conn()
    session = create_db_session(engine)
    q2 = Quake2(session)
    loop = asyncio.get_event_loop()
    MasterServer.console_output(f"Starting master server")
    listen = loop.create_datagram_endpoint(MasterServer,
                                           local_addr=('0.0.0.0', 27900))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    MasterServer.console_output(f"Shutting down master server")
    session.close()
    transport.close()
    loop.close()
