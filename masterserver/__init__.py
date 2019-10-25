import logging

from gameserver import GameServer


class MasterServer:
    def __init__(self, storage, protocols):
        logging.debug(f"{self.__class__.__name__ } - Initialising master server.")
        self.transport = None
        self.storage = storage
        self.protocols = protocols

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, address):
        response = None
        logging.debug(f"{self.__class__.__name__ } - Recieved {data} from {address[0]}:{address[1]}")
        headers, *status = data.splitlines()

        result = self.protocols.is_B2M(headers)
        if result:
            response = self.handle_client(result)
        else:
            result = self.protocols.is_S2M(headers)
            response = self.handle_server(result, status, address)

        if response:
            logging.debug(f"{self.__class__.__name__ } - Sending {response} to {address}")
            self.transport.sendto(response, address)

    def handle_client(self, result):
        logging.debug(f"{self.__class__.__name__ } - Header belongs to client")
        response_header = result.get('resp', None)
        server_list = self.storage.list_servers(result.get('game'))
        response = self.create_response(response_header, server_list)
        return response

    def handle_server(self, result, status, address):
        logging.debug(f"{self.__class__.__name__ } - Header belongs to server")
        server = GameServer(address, status, result)
        if self.storage.get_server(server):
            self.storage.update_server(server)
        else:
            self.storage.create_server(server)

        if not server.active:
            self.storage.server_shutdown(server)

        response = result.get('resp', None)
        return response

    @staticmethod
    def create_response(header, response):
        if header:
            response.insert(0, header)
            return b'\n'.join(response)

        return response
