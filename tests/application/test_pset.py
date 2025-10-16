from openprotocol.application.parameter_set import SelectParameterSet
from openprotocol.core.message import OpenProtocolRawMessage


def test_pset_create():
    pset: SelectParameterSet = SelectParameterSet(1)
    result: OpenProtocolRawMessage = pset.encode()
    assert result is not None
    assert isinstance(result, OpenProtocolRawMessage)
    assert result.mid == 18
    assert result.revision == 1
    assert result[20:23] == "1".zfill(3)
    assert 4 in pset.expected_response_mids
