#!/usr/bin/env python3
import asyncio
import ipaddress
import struct

LOCAL = ('127.0.0.1', 27900)
serverlist = {}


class MasterServer:
    header = b'\xff\xff\xff\xff'
    header_ack = b''.join([header, b'ack'])
    header_servers = b''.join([header, b'servers '])

    def connection_made(self, transport):
        self.transport = transport

    def decoder(self, code):
        return code.decode('ascii')

    def dictify(self):
        """
        Byte string -> Byte list -> Byte Tuple list -> Dict String
        TODO: This should really be cleaned up...
              and there's a mistake in one of the examples

        Example input:
        \\cheats\\0\\dmflags\\16\\\0
        Example output:
        [b'cheats', b'0', b'dmflags', b'16']
        """
        bytes_command = self.message[1].split(b'\\')[1:]
        """
        Example output:
        [(b'cheats', b'0'), (b'dmflags', b'16')]
        """
        zipped = zip(bytes_command[0::2], bytes_command[1::2])
        """
        Example output:
        {'cheats': '0', 'dmflags': '16'}
        """
        return dict((self.decoder(x), self.decoder(y)) for x, y in zipped)

    def process_heartbeat(self, address):
        serverlist[address] = self.dictify()

    def process_shutdown(self, address):
        """
        Is this the required behaviour?
        """
        print(f"Shutdown from {address}")
        del serverlist[address]

    def process_ping(self, address):
        print(f"Sending ack to {address}")
        self.transport.sendto(self.header_ack, address)

    def process_query(self, destination):
        print(f"Sending servers to {destination}")
        serverstring = [self.header_servers]
        for server in serverlist.keys():
            ip = int(ipaddress.IPv4Address(server[0]))
            address = struct.pack('!LH', int(ip), server[1])
            serverstring.append(address)

        self.transport.sendto(b''.join(serverstring), destination)

    def datagram_received(self, data, address):
        self.message = data.split(b'\n')
        if self.message[0].startswith(self.header):
            command = self.message[0][4:]
            if command.startswith(b"heartbeat"):
                self.process_heartbeat(address)
            elif command.startswith(b"shutdown"):
                self.process_shutdown(address)
            elif command.startswith(b"ping"):
                self.process_ping(address)
            else:
                print(f"Unknown command: {command}")
        elif self.message[0].startswith(b"query"):
            self.process_query(address)
        else:
            print(f"Unknown command: {command}")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    print("Starting UDP server")
    # One protocol instance will be created to serve all client requests
    listen = loop.create_datagram_endpoint(MasterServer, local_addr=LOCAL)
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()
