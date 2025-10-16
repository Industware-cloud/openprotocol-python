from openprotocol.application.base_messages import OpenProtocolCommandMsg
from openprotocol.core.message import OpenProtocolRawMessage


class SelectParameterSet(OpenProtocolCommandMsg):
    MID = 18
    REVISION = 1

    def __init__(self, id_set: int):
        self._id_set = id_set

    def encode(self) -> OpenProtocolRawMessage:
        return self.create_message(str(self._id_set).zfill(3))
