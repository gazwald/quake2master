from unittest import TestCase
from unittest.mock import patch
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.orm import Base, Server
from masters import Headers, Quake2


class TestQuake2(TestCase):
    def setUp(self):
        self.engine = create_engine('postgresql://test_user:test_pass@localhost:5432/test_q2m')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)

    def test_quake2_process_ping(self):
        q2 = Quake2(self.session)
        result = q2.process_ping(('127.0.0.1', 27910))
        self.assertEqual(result, Headers.q2header_ack)
        self.assertIsInstance(Server, Quake2.get_server(('127.0.0.1', 27910)))
