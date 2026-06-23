# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import models
from odoo.exceptions import AccessDenied, AccessError
from odoo.tools.uuid_utils import to_uuid


class IrWebsocket(models.AbstractModel):
    _inherit = 'ir.websocket'

    def _build_bus_channel_list(self, channels):
        if self.env.uid:
            # Do not alter original list.
            channels = list(channels)
            for channel in channels:
                if isinstance(channel, str):
                    match = re.match(r'editor_collaboration:(\w+(?:\.\w+)*):(\w+):([\w-]+)', channel)
                    if match:
                        model_name = match[1]
                        field_name = match[2]
                        raw_res_id = match[3]
                        # res_id may be an int (legacy int PK models) or a UUID.
                        res_id = int(raw_res_id) if raw_res_id.isdigit() else to_uuid(raw_res_id)

                        # Verify access to the edition channel.
                        if self.env.user._is_public():
                            raise AccessDenied()

                        document = self.env[model_name].browse([res_id])
                        if not document.exists():
                            continue

                        try:
                            document.check_access('read')
                            document.check_access('write')
                            if field := document._fields.get(field_name):
                                document._check_field_access(field, 'read')
                                document._check_field_access(field, 'write')
                        except AccessError:
                            continue

                        channels.append((self.env.registry.db_name, 'editor_collaboration', model_name, field_name, res_id))
        return super()._build_bus_channel_list(channels)
