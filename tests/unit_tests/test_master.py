from unittest import TestCase

from masters import Master


class TestMaster(TestCase):
    def test_master_bytepack(self):
        result = Master.bytepack(('127.0.0.1', 27910))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x7f\x00\x00\x01m\x06')
        result = Master.bytepack(('1.1.1.1', 1000))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x01\x01\x01\x01\x03\xe8')
        result = Master.bytepack(('254.254.254.254', 65535))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\xfe\xfe\xfe\xfe\xff\xff')

    def test_master_is_q2(self):
        self.assertTrue(Master.is_q2(b'\xff\xff\xff\xffping'))
        self.assertTrue(Master.is_q2(b'\xff\xff\xff\xffheartbeat'))
        self.assertTrue(Master.is_q2(b'\xff\xff\xff\xffshutdown'))
        self.assertTrue(Master.is_q2(b'query'))
        self.assertFalse(Master.is_q2(b'garbage'))
        self.assertFalse(Master.is_q2(b'\xff\xff\xff\xff'))
        self.assertFalse(Master.is_q2(b'\xff\xff\xff\xffgarbage'))
