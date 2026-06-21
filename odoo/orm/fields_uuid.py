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
    #
    # NOTE: do NOT override __get__. A previous version returned ``record._ids[0]``
    # (the record's own primary key) for every Uuid field, so a non-id value field
    # such as a reference ``res_id`` read back the record's own id instead of its
    # stored value. Inherit the standard Field.__get__, which reads the field
    # value from cache.

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
        if isinstance(value, BaseModel):
            # a recordset assigned to a reference field (e.g. res_id) -> its id
            # (empty recordset -> False -> treated as no value)
            value = value.id or None
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
