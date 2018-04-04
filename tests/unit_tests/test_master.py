from unittest import TestCase

from masters import idCommon


class TestidCommon(TestCase):
    def test_master_bytepack(self):
        result = idCommon.bytepack(('127.0.0.1', 27910))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x7f\x00\x00\x01m\x06')
        result = idCommon.bytepack(('1.1.1.1', 1000))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x01\x01\x01\x01\x03\xe8')
        result = idCommon.bytepack(('254.254.254.254', 65535))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\xfe\xfe\xfe\xfe\xff\xff')

    def test_master_is_q2(self):
        self.assertTrue(idCommon.is_q2(b'\xff\xff\xff\xffping'))
        self.assertTrue(idCommon.is_q2(b'\xff\xff\xff\xffheartbeat'))
        self.assertTrue(idCommon.is_q2(b'\xff\xff\xff\xffshutdown'))
        self.assertTrue(idCommon.is_q2(b'query'))
        self.assertFalse(idCommon.is_q2(b'garbage'))
        self.assertFalse(idCommon.is_q2(b'\xff\xff\xff\xff'))
        self.assertFalse(idCommon.is_q2(b'\xff\xff\xff\xffgarbage'))
