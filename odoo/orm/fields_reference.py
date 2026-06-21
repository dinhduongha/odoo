from collections import defaultdict
from operator import attrgetter
import uuid
import logging
import traceback

from odoo.tools import OrderedSet, unique
from odoo.tools.sql import pg_varchar

from .fields import Field
from .fields_selection import Selection
from .fields_uuid import Uuid
from .models import BaseModel

_logger = logging.getLogger('odoo.fields_reference')

class Reference(Selection):
    """Pseudo-relational field (no FK in database)."""
    type = 'reference'
    _column_type = ('varchar', pg_varchar())

    def convert_to_column(self, value, record, values=None, validate=True):
        return Field.convert_to_column(self, value, record, values, validate)

    def convert_to_cache(self, value, record, validate=True):
        # cache format: str ("model,id") or None
        if isinstance(value, BaseModel):
            if not validate or (value._name in self.get_values(record.env) and len(value) <= 1):
                return "%s,%s" % (value._name, value.id) if value else None
        elif isinstance(value, str):
            res_model, res_id = value.split(',')
            if not validate or res_model in self.get_values(record.env):
                try:
                    val_uuid = uuid.UUID(res_id)
                    if record.env[res_model].browse(val_uuid).exists():
                        return value
                except Exception:
                    return None
        elif not value:
            return None
        raise ValueError("Wrong value for %s: %r" % (self, value))

    def convert_to_record(self, value, record):
        if value:
            res_model, res_id = value.split(',')
            try:
                return record.env[res_model].browse(uuid.UUID(res_id))
            except Exception:
                return None
        return None

    def convert_to_read(self, value, record, use_display_name=True):
        return "%s,%s" % (value._name, value.id) if value else False

    def convert_to_export(self, value, record):
        return value.display_name if value else ''

    def convert_to_display_name(self, value, record):
        return value.display_name if value else False


class Many2oneReference(Field[uuid.UUID]):
#class Many2oneReference(Uuid):
    """Pseudo-relational field (UUID primary key)."""
    type = 'many2one_reference'
    _column_type = ('uuid', 'uuid')
    model_field = None
    aggregator = None

    _related_model_field = property(attrgetter('model_field'))
    _description_model_field = property(attrgetter('model_field'))

    # def convert_to_cache(self, value, record, validate=True):
    #     if isinstance(value, BaseModel):
    #         value = value._ids[0] if value._ids else None
        
    #     if isinstance(value, str):
    #         try:
    #             value = uuid.UUID(value)
    #         except Exception:
    #             value = None
    #     return super().convert_to_cache(value, record, validate)
    
    def convert_to_read(self, value, record, use_display_name=True):
        """
        Convert stored value (UUID) → Python value for reading.
        Ensure we don't fallback to record.id if cache not yet populated.
        """
        if isinstance(value, BaseModel):
            # lấy id của record
            value_id = value.id if value._ids else None
        elif isinstance(value, uuid.UUID):
            value_id = value
        elif value is None:
            value_id = None
        else:
            # fallback: có thể tuple (id, name)
            try:
                value_id = uuid.UUID(str(value))
            except Exception:
                value_id = None

        # empty relational value reads as False (ORM convention), not None
        return value_id or False

    # UUIDv7 Patch
    def convert_to_cache(self, value, record, validate=True):
        # if record and record._name == "ir.model.data":
        #     stack = ''.join(traceback.format_stack()[:-1])  # Bỏ dòng hiện tại    
        #     _logger.warning(
        #         "[UUID DEBUG] convert_to_cache [BEFORE] model=%s field=%s raw_value=%r type=%s\n",
        #         record._name, self.name, value, type(value)
        #     )
            # _logger.warning(
            #     "[UUID DEBUG] convert_to_cache [Stack] model=%s stack=%s\n",
            #     record._name, stack
            # )
        # cache format: id or None
        # if type(value) is int or type(value) is NewId:
        #     id_ = value
        # elif
        if isinstance(value, BaseModel):
            if validate and (value._name != self.comodel_name or len(value) > 1):
                raise ValueError("Wrong value for %s: %r" % (self, value))
            id_ = value._ids[0] if value._ids else None
        elif isinstance(value, uuid.UUID):
            id_ = value
        elif isinstance(value, str):
            try:
                id_ = uuid.UUID(value)
            except Exception:
                id_ = None    
        elif isinstance(value, tuple):
            # value is either a pair (id, name), or a tuple of ids
            id_ = value[0] if value else None
        elif isinstance(value, dict):
            # return a new record (with the given field 'id' as origin)
            comodel = record.env[self.comodel_name]
            origin = comodel.browse(value.get('id'))
            id_ = comodel.new(value, origin=origin).id
        else:
            id_ = None

        # if self.delegate and record and not any(record._ids):
        #     # if all records are new, then so is the parent
        #     id_ = id_ and NewId(id_)

        return id_    

    def _update_inverses(self, records: BaseModel, value):
        if not value:
            return
        model_ids = self._record_ids_per_res_model(records)

        for invf in records.pool.field_inverses[self]:
            records_browse = records.browse(model_ids[invf.model_name])
            if not records_browse:
                continue
            corecord = records_browse.env[invf.model_name].browse(value)
            records_browse = records_browse.filtered_domain(invf.get_comodel_domain(corecord))
            if not records_browse:
                continue
            ids0 = invf._get_cache(corecord.env).get(corecord.id)
            if ids0 is not None or not corecord.id:
                ids1 = tuple(unique((ids0 or ()) + records_browse._ids))
                invf._update_cache(corecord, ids1)

    def _record_ids_per_res_model(self, records: BaseModel) -> dict[str, OrderedSet]:
        model_ids = defaultdict(OrderedSet)
        for record in records:
            model = record[self.model_field]
            if not model and record._fields[self.model_field].compute:
                record._fields[self.model_field].compute_value(record)
                model = record[self.model_field]
                if not model:
                    continue
            model_ids[model].add(record.id)
        return model_ids

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
        #raise ValueError(f"Invalid UUID for Many2oneReference {self.name}: {value!r}")