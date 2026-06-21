# odoo/orm/fields_uuid.py
import logging
import uuid

from odoo.tools.uuid_utils import uuid7, to_uuid
from .fields import Field
from .models import BaseModel

_logger = logging.getLogger(__name__)


class Uuid(Field[uuid.UUID]):
    """uuid7 field for primary keys in Odoo models."""

    type = 'uuid'
    column_type = ('uuid', 'uuid')

    # NOTE: do NOT auto-default to uuid7(). The primary-key id uses the dedicated
    # Id field (DB-side ``DEFAULT uuidv7()``); every fields.Uuid is a regular,
    # usually nullable, value/reference field. A model that wants a generated
    # default must set ``default=lambda _: uuid7()`` explicitly.

    def __get__(self, record, owner=None):
        if record is None:
            return self
        # avoid recursion: read _ids directly
        ids = object.__getattribute__(record, "_ids")
        size = len(ids)
        if size == 0:
            return False
        elif size == 1:
            return ids[0]
        raise ValueError(f"Expected singleton: {record}")

    def convert_to_column(self, value, record, values=None, validate=True):
        """Python-side value -> DB column (uuid string)."""
        if value is None:
            return None
        if isinstance(value, BaseModel):
            value = value.id
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            return value
        return None

    def convert_to_record(self, value, record):
        return to_uuid(value) if value else None

    def convert_to_cache(self, value, record=None, validate=True):
        """DB/column value -> cache value (Python side, uuid.UUID)."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                _logger.warning("Invalid UUID string for %s: %r", self.name, value)
                return value
        return value
