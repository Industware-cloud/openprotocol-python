import unittest
from openprotocol.core.message import OpenProtocolMessage


class TestOpenProtocolMessage(unittest.TestCase):
    def test_basic_encode_decode(self):
        msg = OpenProtocolMessage(mid=61, revision=1, payload="ABCDEF")
        raw = msg.encode()
        decoded = OpenProtocolMessage.decode(raw)

        self.assertEqual(decoded._mid, 61)
        self.assertEqual(decoded._revision, 1)
        self.assertEqual(decoded._payload, "ABCDEF")
        self.assertEqual(decoded._station_id, 1)  # default

    def test_station_id_default_spaces(self):
        # Station 1 represented as two spaces
        msg = OpenProtocolMessage(mid=61, revision=1, payload="TEST", station_id=1)
        raw = msg.encode()
        self.assertIn(b"  ", raw)  # two spaces in header

        decoded = OpenProtocolMessage.decode(raw)
        self.assertEqual(decoded._station_id, 1)

    def test_station_id_custom(self):
        msg = OpenProtocolMessage(mid=61, revision=1, payload="PAYLOAD", station_id=5)
        raw = msg.encode()
        decoded = OpenProtocolMessage.decode(raw)
        self.assertEqual(decoded._station_id, 5)

    def test_round_trip_with_all_fields(self):
        msg = OpenProtocolMessage(
            mid=9999, revision=2, payload="HELLO", station_id=12, spindle_id=3, seq_no=7
        )
        raw = msg.encode()
        decoded = OpenProtocolMessage.decode(raw)

        self.assertEqual(decoded._mid, 9999)
        self.assertEqual(decoded._revision, 2)
        self.assertEqual(decoded._payload, "HELLO")
        self.assertEqual(decoded._station_id, 12)
        self.assertEqual(decoded._spindle_id, 3)
        self.assertEqual(decoded._seq_no, 7)
