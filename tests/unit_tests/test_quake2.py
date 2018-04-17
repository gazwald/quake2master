from unittest import TestCase
from unittest.mock import patch
import logging

from games.shared import idTechCommon
from games import Quake2Master


class TestQuake2Master(TestCase):
    def setUp(self):
        self.q2 = Quake2Master(None)

    def tearDown(self):
        del self.q2

    def test_quake2(self):
        self.assertIsInstance(self.q2, Quake2Master)

    def test_quake2_process_request(self):
        logging.disable(logging.CRITICAL)
        result = self.q2.process_request(b'garbage', ('127.0.0.1', 29710))
        self.assertEqual(result, None)

    def test_quake2_process_request_log(self):
        logging.disable(logging.NOTSET)
        with self.assertLogs(level='INFO') as cm:
            self.q2.process_request(b'garbage', ('127.0.0.1', 29710))
        self.assertEqual(cm.output, ["WARNING:root:Unknown message: [b'garbage']"])

    @patch('games.Quake2Master.process_query')
    def test_quake2_process_request_query(self, MockProcessQuery):
        self.q2.process_request(idTechCommon.headers['quake2']['query'], ('127.0.0.1', 29710))
        assert Quake2Master.process_query.called

    @patch('games.Quake2Master.process_ping')
    def test_quake2_process_request_ping(self, MockProcessPing):
        self.q2.process_request(idTechCommon.headers['quake2']['ping'], ('127.0.0.1', 29710))
        assert Quake2Master.process_ping.called

    @patch('games.Quake2Master.process_shutdown')
    def test_quake2_process_request_shutdown(self, MockProcessShutdown):
        self.q2.process_request(idTechCommon.headers['quake2']['shutdown'], ('127.0.0.1', 29710))
        assert Quake2Master.process_shutdown.called

    @patch('games.Quake2Master.process_heartbeat')
    def test_quake2_process_request_heartbeat(self, MockProcessHeartbeat):
        self.q2.process_request(idTechCommon.headers['quake2']['heartbeat'], ('127.0.0.1', 29710))
        assert Quake2Master.process_heartbeat.called
