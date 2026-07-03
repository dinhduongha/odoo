# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    def action_mass_mailing_attendees(self):
        # uuid: str() the ids so repr emits quoted strings, not UUID(...) (a
        # non-literal the mailing_domain / JS domain parser would reject)
        domain = repr([('slide_channel_ids', 'in', [str(cid) for cid in self.ids])])
        mass_mailing_action = dict(
            name=_('Mass Mail Course Members'),
            type='ir.actions.act_window',
            res_model='mailing.mailing',
            view_mode='form',
            target='current',
            context=dict(
                default_mailing_model_id=self.env.ref('base.model_res_partner').id,
                default_mailing_domain=domain,
            ),
        )
        return mass_mailing_action
