# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, tools
from odoo.addons.web.models.ir_ui_menu import _str_id
from odoo.http import request


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('self.env.uid', 'self.env.lang', 'self.env.context.get("force_action")')
    def load_menus_root(self):
        root_menus = super().load_menus_root()
        if self.env.context.get('force_action'):
            web_menus = self.load_web_menus(request.session.debug if request else False)
            for menu in root_menus['children']:
                # uuidv7 PKs: web_menus is keyed by stringified ids (JSON object
                # keys are always strings) while root_menus carries raw uuid ids.
                web_menu = web_menus[_str_id(menu['id'])]
                # Force the action.
                if (
                    not menu['action']
                    and web_menu['actionModel']
                    and web_menu['actionID']
                ):
                    menu['action'] = f"{web_menu['actionModel']},{web_menu['actionID']}"

        return root_menus
