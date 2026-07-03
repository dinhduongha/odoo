# odoo/tools/uuid_utils.py
import os
import threading
import time
import uuid

# Monotonic uuid7 generator (RFC 9562, method 1 - replace leftmost random bits
# with an incrementing counter). Odoo assigns primary-key ids in Python at create
# time (orm/models.py _create) and relies on id order == creation order, because
# the default record _order ends with ", id". A plain time-then-random uuid7 only
# orders at millisecond granularity, so records created within the same millisecond
# (the norm for batched create([...])) would sort randomly, silently reshuffling
# recordsets vs creation order. That breaks order-sensitive logic (e.g. the tax
# engine's cent-remainder distribution across tied lines). Making uuid7 strictly
# monotonic restores the "ids increase with creation" guarantee that integer PKs
# gave for free, matching PostgreSQL's own monotonic uuidv7().
_uuid7_lock = threading.Lock()
_uuid7_last_ms = -1
_uuid7_counter = 0
# 18-bit per-millisecond counter spanning rand_a (12 bits) + 6 high bits of rand_b.
_UUID7_COUNTER_MAX = (1 << 18) - 1


def uuid7() -> uuid.UUID:
    global _uuid7_last_ms, _uuid7_counter
    with _uuid7_lock:
        ms = int(time.time() * 1000)
        if ms <= _uuid7_last_ms:
            # Same (or backwards) millisecond: bump the counter to stay monotonic.
            _uuid7_counter += 1
            if _uuid7_counter > _UUID7_COUNTER_MAX:
                # Counter exhausted within a millisecond: advance the timestamp.
                _uuid7_last_ms += 1
                _uuid7_counter = 0
                ms = _uuid7_last_ms
            else:
                ms = _uuid7_last_ms
        else:
            _uuid7_last_ms = ms
            _uuid7_counter = 0
        counter = _uuid7_counter

    # Layout: 48-bit unix_ts_ms | 12-bit counter_high | 62-bit (6-bit counter_low + random)
    rand_bytes = bytearray(os.urandom(10))
    counter_high = (counter >> 6) & 0xFFF  # top 12 bits -> rand_a
    counter_low = counter & 0x3F           # bottom 6 bits -> high bits of rand_b
    uuid_bytes = bytearray(ms.to_bytes(6, "big") + bytes(rand_bytes))
    # rand_a (bytes 6-7, low 12 bits): set version nibble + counter_high
    uuid_bytes[6] = 0x70 | (counter_high >> 8)        # version 7 + counter_high[11:8]
    uuid_bytes[7] = counter_high & 0xFF               # counter_high[7:0]
    # rand_b high byte (byte 8): variant + 6-bit counter_low
    uuid_bytes[8] = 0x80 | (counter_low & 0x3F)       # variant 1 + counter_low
    return uuid.UUID(bytes=bytes(uuid_bytes))

def is_uuid(value: str) -> bool:
    """Kiểm tra chuỗi có phải UUID hợp lệ không."""
    # Non-string inputs (int route default of 0, missing kwarg -> None, or an
    # already-parsed UUID) are not uuid strings; guard so callers can pass raw
    # params without pre-checking (uuid.UUID(0) would raise AttributeError).
    if isinstance(value, uuid.UUID):
        return True
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def to_uuid(v):
    if isinstance(v, str) and is_uuid(v):
        return uuid.UUID(v)
    return v