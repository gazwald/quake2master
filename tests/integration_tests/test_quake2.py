from unittest import TestCase
import logging

from database.orm import Base
from database.functions import (create_db_conn,
                                create_db_session)

from masters import Headers, Quake2


class TestQuake2(TestCase):
    def setUp(self):
        logging.disable(logging.NOTSET)

        self.engine = create_db_conn('testing')
        Base.metadata.create_all(self.engine)
        self.session = create_db_session(self.engine)

        self.address1 = ('127.0.0.10', 1337)
        self.server1 = ('127.0.0.1', 27910)
        self.server2 = ('127.0.0.2', 27920)
        self.server3 = ('127.0.0.3', 27930)
        self.server4 = ('127.0.0.4', 27940)

        self.q2 = Quake2(self.session)

    def tearDown(self):
        del self.q2
        Base.metadata.drop_all(self.engine)
        self.session.close()
        del self.engine

    def test_quake2_process_ping(self):
        """
        Establish server2 as inactive
        Process a ping from both server1 and server2
        Results for both should be the same
        However server2 should now be marked active
        """
        self.q2.process_heartbeat(self.server2)
        self.q2.process_shutdown(self.server2)

        result = self.q2.process_ping(self.server1)
        self.assertEqual(result, Headers.q2header_ack)

        result = self.q2.process_ping(self.server2)
        self.assertEqual(result, Headers.q2header_ack)

        server = self.q2.get_server(self.server2)
        self.assertTrue(server.active)

    def test_quake2_process_heartbeat(self):
        """
        Process heartbeat does not return anything
        However it should create and set a server
        to active
        """
        self.q2.process_heartbeat(self.server1)

        server = self.q2.get_server(self.server1)
        self.assertTrue(server.active)

    def test_quake2_process_shutdown(self):
        """
        Process shutdown does not return anything
        However it should set as server to inactive
        Requires process_heartbeat to create entry
        """
        result = self.q2.process_heartbeat(self.server1)
        self.assertIsNone(result)

        server = self.q2.get_server(self.server1)
        self.assertFalse(server.active)

    def test_quake2_process_query(self):
        """
        Generates a binary string starting with a header
        and containing a list of servers
        The list should only contain servers 1, 2, and 4.
        """
        self.q2.process_heartbeat(self.server1)
        self.q2.process_heartbeat(self.server2)
        self.q2.process_heartbeat(self.server3)
        self.q2.process_shutdown(self.server3)
        self.q2.process_heartbeat(self.server4)

        expected_result = b''.join([Headers.q2header_servers,
                                    self.q2.bytepack(self.server1),
                                    self.q2.bytepack(self.server2),
                                    self.q2.bytepack(self.server4)])

        result = self.q2.process_query(self.address1)
        self.assertEqual(result, expected_result)
