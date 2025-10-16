import pytest

from openprotocol.application.base_messages import OpenProtocolEvent
from openprotocol.application.tightening import LastTighteningResultData
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage


class TighteningDevice(OpenProtocolEvent):
    MID = 61
    REVISION = 1

    def __init__(self, revision: int | None = None):
        self._revision = revision or TighteningDevice.REVISION

    def encode(self) -> OpenProtocolRawMessage:
        msg = OpenProtocolRawMessage(self.MID, self._revision, "")
        msg.encode()
        msg[20:22] = "01"
        msg[22:26] = "0001"  # cell_id 23-26
        msg[26:28] = "02"
        msg[28:30] = "01"  # channel_id 29-30
        msg[30:32] = "03"
        msg[32:57] = "Test controller"  # 33-57 torque_controller_name
        msg[90:93] = "001"  # pset_number 91-93
        msg[105:107] = "09"
        msg[107:108] = "1"  ## tightening_status 108
        msg[108:110] = "10"
        msg[110:111] = "1"  # torque_status 111 (0=Low,1=OK,2=High)
        msg[113:114] = "1"  # 114 angle_status (0=Low,1=OK,2=High)
        msg[140:146] = "000120"  # torque 141-146
        msg[176:195] = "YYYY-MM-DD:HH:MM:SS"  # timestamp
        return msg

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
