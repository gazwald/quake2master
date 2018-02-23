#!/usr/bin/env python3
import asyncio

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
        message = data.split(b'\n')
        if message[0].startswith(b'stat_ping'):
            reply = self.process_stat(address)
        elif message[0].startswith(self.q2header):
            command = message[0][4:]
            if command.startswith(b"heartbeat"):
                reply = q2.process_heartbeat(address)
            elif command.startswith(b"shutdown"):
                reply = q2.process_shutdown(address)
            elif command.startswith(b"ping"):
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
    Common.console_output(f"Starting master server")

    engine = create_db_conn()
    session = create_db_session(engine)
    q2 = Quake2(session)

    loop = asyncio.get_event_loop()
    listen = loop.create_datagram_endpoint(MasterServer,
                                           local_addr=('0.0.0.0', 27900))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    Common.console_output(f"Shutting down master server")
    session.close()
    transport.close()
    loop.close()
