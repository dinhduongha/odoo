# odoo/orm/fields_uuid.py
import uuid
from odoo.tools.uuid_utils import uuid7, to_uuid
from .fields import Field
from .models import BaseModel

class Uuid(Field[uuid.UUID]):
    """
    uuid7 field for primary keys in Odoo models.
    """

    type = 'uuid'
    column_type = ('uuid', 'uuid')

    def __init__(self, *args, **kwargs):
        # vẫn cho phép các tham số như string, required, default, ...
        if 'default' not in kwargs:
            kwargs['default'] = lambda _: uuid7()
        super().__init__(*args, **kwargs)

    def __get__(self, record, owner=None):
        if record is None:
            return self

        # Tránh đệ quy: truy cập _ids trực tiếp qua __getattribute__
        ids = object.__getattribute__(record, "_ids")
        size = len(ids)
        if size == 0:
            return False
        elif size == 1:
            return ids[0]
        raise ValueError(f"Expected singleton: {record}")

    def convert_to_column(self, value, record, values=None, validate=True):
        """Chuyển Python-side → DB (string)."""
        if value is None:
            return None
        if isinstance(value, BaseModel):
            value = value.id
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            return value
        return None

    # def convert_to_column(self, value, record, values=None, validate=True):
    #     if value is None:
    #         return None
    #     return str(value)
    # def convert_to_column(self, value, record, values=None, validate=True):
    #     """Nhận str, uuid.UUID hoặc record, trả về str."""
    #     if value is None:
    #         return None
    #     # ⚙️ Nếu value là record, lấy id của nó
    #     if hasattr(value, "id"):
    #         value = value.id
    #     # ⚙️ Nếu là list (Command.set([...]))
    #     if isinstance(value, (list, tuple)):
    #         return [str(v.id if hasattr(v, "id") else v) for v in value]
    #     # ⚙️ Chuẩn hóa về str UUID
    #     if isinstance(value, uuid.UUID):
    #         return str(value)
    #     if isinstance(value, str):
    #         return value
    #     raise ValueError(f"Invalid UUID value for {self.name}: {value!r}")

    def convert_to_record(self, value, record):
        return to_uuid(value) if value else None

    # def convert_to_cache(self, value, record=None, validate=True):
    #     # Nếu value là UUID object thì chuyển sang string để JSON-safe
    #     if isinstance(value, uuid.UUID):
    #         return str(value)
    #     return value
    def convert_to_cache(self, value, record=None, validate=True):
        """Convert DB/column value -> cache value (Python side)."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                # Không hợp lệ thì giữ nguyên để debug dễ
                _logger.warning("[UUID DEBUG] Invalid UUID string for id: %r", value)
                return value
        return value    
