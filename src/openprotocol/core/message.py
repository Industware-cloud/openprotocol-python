class OpenProtocolMessage:
    """
    Internal representation of a decoded Open Protocol frame.
    Handles parsing of header and payload according to spec.
    https://s3.amazonaws.com/co.tulip.cdn/OpenProtocolSpecification_R280.pdf
    """

    # Open Protocol spec: header fields (after 4-char length)
    HEADER_SIZE = 20  # minimal, may be longer if optional fields enabled

    def __init__(
        self,
        mid: int,
        revision: int,
        payload: str,
        no_ack_flag: bool = False,
        station_id: int = 1,
        spindle_id: int = 1,
        seq_no: int | None = None,
        no_of_mess_parts: int | None = None,
        message_part_number: int | None = None,
    ):
        self._mid = mid
        self._revision = revision
        self._no_ack_flag = no_ack_flag

        self._payload = payload
        self._station_id = station_id
        self._spindle_id = spindle_id
        self._seq_no = seq_no
        self._no_of_mess_parts = no_of_mess_parts
        self._message_part_number = message_part_number

    @classmethod
    def decode(cls, raw: bytes) -> "OpenProtocolMessage":
        """Decode raw bytes (with length prefix) into header + payload."""
        raw_str = raw.decode("ascii")
        frame_len = int(raw_str[0:4])

        # Header part after length field
        header = raw_str[4 : cls.HEADER_SIZE]
        payload = raw_str[cls.HEADER_SIZE : frame_len]

        mid = int(header[0:4])  # MID
        revision = int(header[4:7])  # Revision
        no_ack_flag = False if header[7:8].strip() == "" else bool(header[7:8])
        station_id = 1 if header[8:10].strip() == "" else int(header[8:10])
        spindle_id = 1 if header[10:12].strip() == "" else int(header[10:12])
        seq_no = None if header[12:14].strip() == "" else int(header[12:14])
        no_of_mess_parts = None if header[14:15].strip() == "" else int(header[14:15])
        message_part_number = (
            None if header[15:16].strip() == "" else int(header[15:16])
        )

        return cls(
            mid,
            revision,
            payload,
            no_ack_flag,
            station_id,
            spindle_id,
            seq_no,
            no_of_mess_parts,
            message_part_number,
        )

    def encode(self) -> bytes:
        # No Ack Flag
        no_ack_str = "1" if self._no_ack_flag else " "
        # Station ID (2 chars, default = "  ")
        station_str = "  " if self._station_id == 1 else f"{self._station_id:02}"
        # Spindle ID (2 chars, default = "  ")
        spindle_str = "  " if self._spindle_id == 1 else f"{self._spindle_id:02}"
        # Seq No (2 chars or "  ")
        seq_str = "  " if self._seq_no is None else f"{self._seq_no:02}"
        # No of Message Parts (1 char or " ")
        parts_str = (
            " " if self._no_of_mess_parts is None else str(self._no_of_mess_parts)
        )
        # Message Part Number (1 char, mandatory)
        part_no_str = (
            " " if self._message_part_number is None else str(self._message_part_number)
        )

        header = (
            f"{self._mid:04}"
            f"{self._revision:03}"
            f"{no_ack_str}"
            f"{station_str}"
            f"{spindle_str}"
            f"{seq_str}"
            f"{parts_str}"
            f"{part_no_str}"
        )

        body = header + self._payload
        frame = f"{len(body) + 4:04}" + body
        return frame.encode("ascii")

    def __repr__(self):
        return f"<OpenProtocolMessage MID={self._mid} REV={self._revision} Payload='{self._payload}'>"

    @property
    def mid(self):
        return self._mid

    @property
    def revision(self):
        return self._revision
