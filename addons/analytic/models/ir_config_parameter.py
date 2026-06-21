# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.uuid_utils import to_uuid


class IrConfigParameter(models.Model):

    _inherit = 'ir.config_parameter'

    def write(self, vals):
        ''' When this paramater is changed, dynamic fields needs to be recomputed '''
        param = self.filtered(lambda x: x.key == 'analytic.project_plan')
        if not param:
            return super().write(vals)
        old_plan_id = param.value
        new_plan_id = vals.get('value')
        # plan ids are uuid; accept the id (uuid or legacy int) and validate the plan exists
        plan = self.env['account.analytic.plan'].browse(to_uuid(new_plan_id)) if new_plan_id else None
        if not (
            plan
            and plan.exists()
            and (plan_field := plan._find_plan_column())
        ):
            raise UserError(_('The value for %s must be the ID to a valid analytic plan that is not a subplan', param.key))
        res = super().write(vals)
        if old_plan_id:
            self.env['account.analytic.plan'].browse(to_uuid(old_plan_id))._sync_all_plan_column()
        plan_field.unlink()
        return res
