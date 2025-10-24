from dataclasses import dataclass
from typing import Callable, Any, List

from openprotocol.core.message import OpenProtocolRawMessage


@dataclass
class FieldSpec:
    def __init__(
        self,
        name: str | None,
        start: int,
        end: int,
        parser: Callable[[str], Any] = lambda s: s,
        default: Any | None = None,
        validator: Callable[[Any], bool] | None = None,
    ):
        self.name = name
        self.start = start
        self.end = end
        self.parser = parser
        self.default = default
        self.validator = validator


def parse_message(
    msg: OpenProtocolRawMessage, obj: object, fields: List[FieldSpec]
) -> None:
    """Parse fields from raw message into object attributes."""
    raw = msg.raw_str
    msg_len = len(raw)

    fields = sorted(fields, key=lambda f: f.start)

    for field_spec in fields:
        if msg_len <= field_spec.end:
            break

        try:
            substr = raw[field_spec.start : min(field_spec.end, msg_len)].strip()
            if not substr and field_spec.default is not None:
                value = field_spec.default
            else:
                value = field_spec.parser(substr)
        except Exception as e:
            raise ValueError(f"Failed to parse field {field_spec.name}: {e}") from e

        if field_spec.validator and value is not None:
            if not field_spec.validator(value):
                raise ValueError(
                    f"Validation failed for field '{field_spec.name}', got {value}"
                )
        if field_spec.name:
            setattr(obj, field_spec.name, value)
