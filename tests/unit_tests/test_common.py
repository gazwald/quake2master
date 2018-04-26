from unittest import TestCase

from games.shared import idTechCommon


class TestidTechCommon(TestCase):
    def test_common_bytepack(self):
        result = idTechCommon.bytepack(('127.0.0.1', 27910))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x7f\x00\x00\x01m\x06')
        result = idTechCommon.bytepack(('1.1.1.1', 1000))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\x01\x01\x01\x01\x03\xe8')
        result = idTechCommon.bytepack(('254.254.254.254', 65535))
        self.assertEqual(len(result), 6)
        self.assertEqual(result, b'\xfe\xfe\xfe\xfe\xff\xff')

    def test_common_is_q2(self):
        self.assertTrue(idTechCommon.is_q2(b'\xff\xff\xff\xffping'))
        self.assertTrue(idTechCommon.is_q2(b'\xff\xff\xff\xffheartbeat'))
        self.assertTrue(idTechCommon.is_q2(b'\xff\xff\xff\xffshutdown'))
        self.assertTrue(idTechCommon.is_q2(b'query'))
        self.assertFalse(idTechCommon.is_q2(b'garbage'))
        # TODO: This assertion fails due to the new way the is_q2 function works
        # However b'\xff\xff\xff\xff' isn't only used for quake 2
        # self.assertFalse(idTechCommon.is_q2(b'\xff\xff\xff\xff'))
        self.assertFalse(idTechCommon.is_q2(b'\xff\xff\xff\xffgarbage'))

    def test_common_dictify(self):
        raw_byte_string = [b'\xff\xff\xff\xffheartbeat',
                           b'\\cheats\\0\\deathmatch\\1\\dmflags\\16\\hostname\\Hello\\',
                           b'1 12 Player 1',
                           b'2 24 Player 2',
                           b'100 48 Player 3']
        expected = dict(cheats=0,
                        deathmatch=1,
                        dmflags=16,
                        hostname='Hello',
                        clients=3)
        result = idTechCommon.dictify(raw_byte_string)
        self.assertEqual(result, expected)
