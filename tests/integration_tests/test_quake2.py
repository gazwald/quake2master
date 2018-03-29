from unittest import TestCase
# from unittest.mock import patch
# import logging

from database.orm import Base
from database.functions import (create_db_conn,
                                create_db_session)

from masters import Headers, Quake2


class TestQuake2(TestCase):
    def setUp(self):
        engine = create_db_conn('testing')
        Base.metadata.create_all(engine)
        self.session = create_db_session(engine)

    def test_quake2_process_ping(self):
        q2 = Quake2(self.session)
        result = q2.process_ping(('127.0.0.1', 27910))
        self.assertEqual(result, Headers.q2header_ack)
