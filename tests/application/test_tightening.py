import pytest

from openprotocol.application.base_messages import OpenProtocolEvent
from openprotocol.application.tightening import LastTighteningResultData
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage


class TighteningDevice(OpenProtocolEvent):
    MID = 61
    REVISION = 1

    def __init__(self, revision: int | None = None):
        super().__init__(revision)
        self._revision = revision or TighteningDevice.REVISION

    def encode(self) -> OpenProtocolRawMessage:
        payload = list(" " * 175)
        payload[0:2] = "01"
        payload[2:6] = "0001"  # cell_id 23-26
        payload[6:8] = "02"
        payload[8:10] = "01"  # channel_id 29-30
        payload[10:12] = "03"
        payload[12:37] = "Test controller".ljust(
            37 - 12
        )  # 33-57 torque_controller_name
        payload[70:73] = "001"  # pset_number 91-93
        payload[85:87] = "09"
        payload[87:88] = "1"  ## tightening_status 108
        payload[88:90] = "10"
        payload[90:91] = "1"  # torque_status 111 (0=Low,1=OK,2=High)
        payload[93:94] = "1"  # 114 angle_status (0=Low,1=OK,2=High)
        payload[120:126] = "000120"  # torque 141-146
        payload[156:175] = "YYYY-MM-DD:HH:MM:SS"  # timestamp
        return self.create_message(self._revision, "".join(payload))

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        pass


def test_tightening_rev1_decode():
    tightening = LastTighteningResultData.from_message(TighteningDevice().encode())
    assert tightening is not None
    assert isinstance(tightening, OpenProtocolMessage)
    assert tightening.tightening_status == 1
    assert tightening.pset_number == 1
    assert tightening.torque == 1.2


def test_tightening_decode_notsupported_revision():
    with pytest.raises(NotImplementedError):
        LastTighteningResultData.from_message(TighteningDevice(999).encode())


def test_tightening_decode():
    raw_data = (
        b"050600610051        010000020003STa 6000                 04                         "
        b"0500000600507180800000090000100000110122130141151161171181191200000000000210007502200750023000000240000002500000260999927000002800000290000030000003100000320003300034000350000003600000037000000380000003900000040000000410000000532420000043000004442250888      "
        b"452023-05-15:21:35:0546                   47QuickPset 5              481490150                         51                         52                         530000\x00"
    )
    raw_msg = OpenProtocolRawMessage.decode(raw_data)
    assert raw_msg is not None
    data: LastTighteningResultData = LastTighteningResultData.from_message(raw_msg)

    assert raw_msg.revision == 5
    assert data.pset_number == 5
    assert data.tightening_status == 0
    assert data.angle_status == 1
    assert data.torque_status == 0
    assert data.torque == 0.0
    assert data.angle == 0
    assert data.torque_controller_name == "STa 6000"
    assert data.pset_name == "QuickPset 5"
    assert data.timestamp.startswith("2023-05-15")
    assert data.tool_serial_number == "42250888"
    assert data.torque_value_unit == LastTighteningResultData.TorqueValueUnit.NM


def test_tightening_decode2():
    raw_data = b"038500610021        010000020003STa 6000                 04                         0500000600307130800000090001100001110120130141151161171181191200000000000210013502200165023000000240012342500000260000027000002800000290000030000003100000320003300034000350000003600000037000000380000003900000040000000410000000675420000043000004442250888    \x01\x01452023-10-09:23:35:2346                   \x00"
    raw_msg = OpenProtocolRawMessage.decode(raw_data)
    assert raw_msg is not None
    data: LastTighteningResultData = LastTighteningResultData.from_message(raw_msg)

    assert raw_msg.revision == 2
    assert data.pset_number == 3
    assert data.tightening_status == 0
    assert data.angle_status == 1
    assert data.torque_status == 0
    assert data.torque == 12.34
    assert data.angle == 0
    assert data.torque_controller_name == "STa 6000"
    assert data.pset_name == ""
    assert data.timestamp.startswith("2023-10-09")
    assert data.tool_serial_number == "42250888"
    assert data.torque_value_unit == LastTighteningResultData.TorqueValueUnit.NM
