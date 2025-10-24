import logging
import string
from enum import Enum, verify, UNIQUE

from openprotocol.application.base_messages import (
    OpenProtocolEventSubscribe,
    OpenProtocolEvent,
    OpenProtocolEventACK,
    OpenProtocolEventUnsubscribe,
)
from openprotocol.application.parser import FieldSpec, parse_message
from openprotocol.core.message import OpenProtocolRawMessage
from openprotocol.core.mid_base import OpenProtocolMessage

logger = logging.getLogger(__name__)


class LastTighteningResultDataSubscribe(OpenProtocolEventSubscribe):
    MID = 60
    REVISION = 2
    MID_EVENT = 61

    def __init__(self) -> None:
        super().__init__(self.REVISION)

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION)

    @classmethod
    def from_message(cls, msg: OpenProtocolRawMessage) -> "OpenProtocolMessage":
        return cls()


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

    def __init__(self, revision: int):
        super().__init__(revision)
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
        msg_obj = cls(msg.revision)
        if msg.revision == 1:
            msg_obj._rev1(msg)
        elif 2 <= msg.revision <= 998:
            msg_obj._rev2(msg)
        else:
            raise NotImplementedError(f"Not supported revision {msg.revision}")

        return msg_obj

    def _rev_common(self, msg: OpenProtocolRawMessage):
        fields_common = [
            FieldSpec("cell_id", 20, 22, parser=int),
            FieldSpec("channel_id", 26, 28, parser=int),
            FieldSpec("torque_controller_name", 32, 57, parser=lambda s: s.strip()),
        ]

        parse_message(msg, self, fields_common)

    def _rev1(self, msg: OpenProtocolRawMessage):
        fields_v1 = [
            FieldSpec("pset_number", 90, 93, parser=int),
            FieldSpec(None, 105, 107, parser=str, validator=lambda x: x == "09"),
            FieldSpec("tightening_status", 107, 108, parser=int),
            FieldSpec(None, 108, 110, parser=str, validator=lambda x: x == "10"),
            FieldSpec("torque_status", 110, 111, parser=int),
            FieldSpec("angle_status", 113, 114, parser=int),
            FieldSpec("torque", 140, 146, parser=lambda s: float(s) / 100.0),
            FieldSpec("timestamp", 176, 195, parser=lambda s: s.strip()),
        ]

        self._rev_common(msg)
        parse_message(msg, self, fields_v1)

    def _rev2(self, msg: OpenProtocolRawMessage):
        fields_v2 = [
            FieldSpec("pset_number", 92, 95, parser=int),
            FieldSpec(None, 118, 120, parser=str, validator=lambda x: x == "11"),
            FieldSpec("tightening_status", 120, 121, parser=int),
            FieldSpec(None, 124, 126, parser=str, validator=lambda x: x == "13"),
            FieldSpec("torque_status", 126, 127, parser=int),
            FieldSpec("angle_status", 129, 130, parser=int),
            FieldSpec("torque", 183, 189, parser=lambda s: float(s) / 100.0),
            FieldSpec("angle", 212, 217, parser=int),
            FieldSpec(
                "tool_serial_number",
                329,
                343,
                parser=lambda s: "".join(c for c in s if c in string.printable).strip(),
            ),
            FieldSpec("timestamp", 345, 364, parser=lambda s: s.strip()),
            FieldSpec(None, 385, 387, parser=str, validator=lambda x: x == "47"),
            FieldSpec("pset_name", 387, 412, parser=lambda s: s.strip()),
            FieldSpec(
                "torque_value_unit",
                414,
                415,
                parser=lambda s: LastTighteningResultData.TorqueValueUnit(int(s)),
            ),
        ]

        self._rev_common(msg)
        parse_message(msg, self, fields_v2)

    def encode(self) -> OpenProtocolRawMessage:
        raise NotImplementedError("Not implemented")


class LastTighteningResultDataACK(OpenProtocolEventACK):
    MID = 62
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION)


class LastTighteningResultDataUnsubscribe(OpenProtocolEventUnsubscribe):
    MID = 63
    REVISION = 1

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(self.REVISION)
