import logging
from enum import Enum, verify, UNIQUE

from openprotocol.application.base_messages import (
    OpenProtocolEventSubscribe,
    OpenProtocolEvent,
    OpenProtocolEventACK,
    OpenProtocolEventUnsubscribe,
)
from openprotocol.core.message import OpenProtocolRawMessage

logger = logging.getLogger(__name__)


class LastTighteningResultDataSubscribe(OpenProtocolEventSubscribe):
    MID = 60

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message()


class LastTighteningResultData(OpenProtocolEvent):
    MID = 61

    @verify(UNIQUE)
    class TorqueValueUnit(Enum):
        NM = (1, "Nm")
        LBF_FT = (2, "Lbf.ft")
        LBF_IN = (3, "Lbf.in")
        KPM = (4, "Kpm")
        KGF_CM = (5, "Kgf.cm")
        OZF_IN = (6, "ozf.in")
        PERCENT = (7, "%")
        NCM = (8, "Ncm")

        def __new__(cls, value: int, description: str):
            obj = object.__new__(cls)
            obj._value_ = value  # <- makes .value the integer only
            obj.description = description  # <- add human-readable name
            return obj

        def __str__(self):
            return self.description

    def __init__(self):
        self.final_torque = ""
        self.tightening_status_field = ""
        self.tightening_status = 0
        self.cell_id = 0
        self.channel_id = 0
        self.job_id = 0
        self.pset_number = 0
        self.pset_name = ""
        self.torque_controller_name = ""
        self.result_status = ""
        self.timestamp = ""
        self.angle: int = 0
        self.torque_status = 0
        self.angle_status = 0
        self.torque: float = 0.0
        self.tool_serial_number = ""
        self.torque_value_unit: LastTighteningResultData.TorqueValueUnit = (
            LastTighteningResultData.TorqueValueUnit.NM
        )

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "LastTighteningResultData":
        msg_obj = cls()
        if msg.revision == 1:
            msg_obj._rev1(msg)
        elif 2 <= msg.revision <= 998:
            msg_obj._rev2(msg)
        else:
            raise NotImplementedError(f"Not supported revision {msg.revision}")

        return msg_obj

    def _rev_common(self, msg: OpenProtocolRawMessage):
        if msg[20:22] != "01":
            raise RuntimeError(f"Byte 21-22 is not 01 {msg[20:22]}")
        self.cell_id = int(msg[22:26])  # 23-26

        if msg[26:28] != "02":
            raise RuntimeError(f"Byte 27-28 is not 02 {msg[26:28]}")
        self.channel_id = int(msg[28:30])  # 29-30

        self.torque_controller_name = msg[32:57].strip()  # 33-57

    def _rev1(self, msg: OpenProtocolRawMessage):
        self._rev_common(msg)
        self.pset_number = int(msg[90:93])  # 91-93
        if msg[105:107] != "09":
            raise RuntimeError(f"Byte 106-107 is not 09 {msg[105:107]}")
        self.tightening_status = int(msg[107:108])  ## 108
        if msg[108:110] != "10":  # 109-110
            raise RuntimeError(f"Byte 109-110 is not 10 {msg[108:110]}")
        self.torque_status = int(msg[110:111])  # 111 (0=Low,1=OK,2=High)
        self.angle_status = int(msg[113:114])  # 114 (0=Low,1=OK,2=High)
        self.torque = float(msg[140:146]) / 100.0  # 141-146
        self.timestamp = msg[176:195]

    def _rev2(self, msg: OpenProtocolRawMessage):
        self._rev_common(msg)
        self.pset_number = int(msg[92:95])  # 93-95
        if msg[118:120] != "11":
            raise RuntimeError(f"Byte 119-120 is not 11 {msg[118:120]}")
        self.tightening_status = int(msg[120:121])  ## 121
        if msg[124:126] != "13":  # 125-126
            raise RuntimeError(f"Byte 125-126 is not 13 {msg[124:126]}")
        self.torque_status = int(msg[126:127])  # 127 (0=Low,1=OK,2=High)
        self.angle_status = int(msg[129:130])  # 130 (0=Low,1=OK,2=High)
        self.torque = float(msg[183:189]) / 100.0  # 184-189
        self.angle = int(msg[212:217])  # 213 - 217
        self.tool_serial_number = msg[329:343].strip()  # 330 - 343
        self.timestamp = msg[345:364]  # 346-364
        if msg[385:387] != "47":
            raise RuntimeError(f"Byte 386-387 is not 47 {msg[385:387]}")
        self.pset_name = msg[387:412].strip()  # 388 - 412
        self.torque_value_unit = LastTighteningResultData.TorqueValueUnit(
            int(msg[414:415])
        )  # 415

    def encode(self) -> OpenProtocolRawMessage:
        raise NotImplementedError("Not implemented")


class LastTighteningResultDataACK(OpenProtocolEventACK):
    MID = 62
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message()


class LastTighteningResultDataUnsubscribe(OpenProtocolEventUnsubscribe):
    MID = 63
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message()
