# odoo/tools/uuid_utils.py
import os
import time
import uuid

if hasattr(uuid, "uuid7"):
    uuid7 = uuid.uuid7
else:
    def uuid7() -> uuid.UUID:
        unix_ts_ms = int(time.time() * 1000)
        time_bytes = unix_ts_ms.to_bytes(6, "big")
        rand_bytes = os.urandom(10)
        uuid_bytes = bytearray(time_bytes + rand_bytes)
        uuid_bytes[6] = (uuid_bytes[6] & 0x0F) | 0x70  # version 7
        uuid_bytes[8] = (uuid_bytes[8] & 0x3F) | 0x80  # variant 1
        return uuid.UUID(bytes=bytes(uuid_bytes))

def is_uuid(value: str) -> bool:
    """Kiểm tra chuỗi có phải UUID hợp lệ không."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def to_uuid(v):
    if isinstance(v, str) and is_uuid(v):
        return uuid.UUID(v)
    return v