import pytest
from openprotocol.core.message import OpenProtocolRawMessage


def test_basic_encode_decode():
    msg = OpenProtocolRawMessage(mid=61, revision=1, payload="ABCDEF")
    raw = msg.encode()
    decoded = OpenProtocolRawMessage.decode(raw)

    assert decoded._mid == 61
    assert decoded._revision == 1
    assert decoded._payload == "ABCDEF"
    assert decoded._station_id == 1  # default


def test_station_id_default_spaces():
    # Station 1 represented as two spaces
    msg = OpenProtocolRawMessage(mid=61, revision=1, payload="TEST", station_id=1)
    raw = msg.encode()
    assert b"  " in raw  # two spaces in header

    decoded = OpenProtocolRawMessage.decode(raw)
    assert decoded._station_id == 1


def test_station_id_custom():
    msg = OpenProtocolRawMessage(mid=61, revision=1, payload="PAYLOAD", station_id=5)
    raw = msg.encode()
    decoded = OpenProtocolRawMessage.decode(raw)
    assert decoded._station_id == 5


def test_round_trip_with_all_fields():
    msg = OpenProtocolRawMessage(
        mid=9999, revision=2, payload="HELLO", station_id=12, spindle_id=3, seq_no=7
    )
    raw = msg.encode()
    decoded = OpenProtocolRawMessage.decode(raw)

    assert decoded._mid == 9999
    assert decoded._revision == 2
    assert decoded._payload == "HELLO"
    assert decoded._station_id == 12
    assert decoded._spindle_id == 3
    assert decoded._seq_no == 7
