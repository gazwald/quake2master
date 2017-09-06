#!/usr/bin/env python3
import unittest
from mock import patch

import unpack
MasterServer = None
header = b'\xff\xff\xff\xff'
address = ('127.0.0.1', 7000)
fixture_addresses = [
        ('127.0.0.1', 1337),
        ('127.0.0.1', 27910),
        ('127.0.0.1', 27920),
        ('127.0.0.1', 27931),
        ('127.0.0.1', 28000),
        ('1.1.1.1', 1337),
        ('1.1.1.1', 27910),
        ('1.1.1.1', 27920),
        ('1.1.1.1', 27931),
        ('1.1.1.1', 28000),
        ('254.255.255.255', 1337),
        ('254.255.255.255', 27910),
        ('254.255.255.255', 27920),
        ('254.255.255.255', 27931),
        ('254.255.255.255', 28000),
]


class TestMasterServerBytePack(unittest.TestCase):
    @patch('MasterServer.process_heartbeat')
    def test_process_BytePack(self, mock):
        for address in fixture_addresses:
            result = MasterServer.bytepack(address)
            self.assertEqual(result, unpack(address))


class TestMasterServerDatagramRecieved(unittest.TestCase):
    @patch('MasterServer.process_heartbeat')
    def test_process_heartbeat_called(self, mock):
        data = header + b'heartbeat'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertTrue(mock.called)

    @patch('MasterServer.process_heartbeat')
    def test_process_heartbeat_not_called(self, mock):
        data = header + b'shutdown'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertFalse(mock.called)

    @patch('MasterServer.process_shutdown')
    def test_process_shutdown_called(self, mock):
        data = header + b'shutdown'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertTrue(mock.called)

    @patch('MasterServer.process_shutdown')
    def test_process_shutdown_not_called(self, mock):
        data = header + b'ping'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertFalse(mock.called)

    @patch('MasterServer.process_ping')
    def test_process_ping_called(self, mock):
        data = header + b'ping'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertTrue(mock.called)

    @patch('MasterServer.process_ping')
    def test_process_ping_not_called(self, mock):
        data = header + b'heartbeat'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertFalse(mock.called)

    @patch('MasterServer.process_query')
    def test_process_query_called(self, mock):
        data = b'query'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertTrue(mock.called)

    @patch('MasterServer.process_query')
    def test_process_query_not_called(self, mock):
        data = header + b'query'
        MasterServer.datagram_recieved(MasterServer, data, address)
        self.assertFalse(mock.called)


if __name__ == "__main__":
    unittest.main()

