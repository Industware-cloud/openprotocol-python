from openprotocol.application.base_messages import (
    CommunicationNegativeAck,
    CommunicationPositiveAck,
)
from openprotocol.application.communication import (
    CommunicationStartAcknowledge,
)
from openprotocol.application.tightening import LastTighteningResultData
from openprotocol.core.mid_base import register_messages

register_messages(
    CommunicationStartAcknowledge,
    CommunicationNegativeAck,
    CommunicationPositiveAck,
    LastTighteningResultData,
)
