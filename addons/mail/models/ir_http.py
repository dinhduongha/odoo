# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import models
from odoo.http import request
from odoo.tools.uuid_utils import to_uuid
from odoo.addons.mail.tools.discuss import Store

# Canonical uuid pattern, used to robustly parse the '-'-joined 'cids' cookie
# (the separator '-' also appears inside uuids, so a naive split breaks them).
_UUID_RE = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Override to add the current user data (partner or guest) if applicable."""
        result = super().session_info()
        store = Store()
        ResUsers = self.env["res.users"]
        if cids := request.cookies.get("cids", False):
            allowed_company_ids = []
            for company_id in [to_uuid(cid) for cid in _UUID_RE.findall(cids)]:
                if company_id in self.env.user.company_ids.ids:
                    allowed_company_ids.append(company_id)
            ResUsers = self.with_context(allowed_company_ids=allowed_company_ids).env["res.users"]
        ResUsers._init_store_data(store)
        result["storeData"] = store.get_result()
        guest = self.env['mail.guest']._get_guest_from_context()
        if not request.session.uid and guest:
            user_context = {'lang': guest.lang}
            result["user_context"] = user_context
        return result
