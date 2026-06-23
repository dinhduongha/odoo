# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_invoice_reference_si_partner(self):
        """
        Generate the Slovenian structured payment reference using the partner's ID.
        Format: SI01 (P1-P2-P3)K
        - P1: Last two digits of the invoice year
        - P2: Partner ID
        - P3: Journal ID
        - K: Check digit

        :return: the formatted structured reference string (SI01...)
        """
        self.ensure_one()
        # Partner ids are UUIDs; keep only their digits so the segment stays
        # purely numeric as required by the SI01 structured reference format.
        p3 = re.sub(r'\D', '', str(self.partner_id.id)) or '0'
        return self._build_invoice_reference(p3)

    def _get_invoice_reference_si_invoice(self):
        """
        Generate the Slovenian structured payment reference using the invoice sequence number.

        Format: SI01 (P1-P2-P3)K
        - P1: Last two digits of the invoice year
        - P2: Trailing digits of the invoice name (sequence number)
        - P3: Journal ID
        - K: Check digit

        :return: the formatted structured reference string (SI01...)
        """
        self.ensure_one()
        match = re.search(r'(\d+)$', self.name or '')
        p3 = str(int(match.group(1))) if match else '0'
        return self._build_invoice_reference(p3)

    def _build_invoice_reference(self, p3):
        """Builds the reference using a shared structure for both methods."""
        # Journal ids are UUIDs; keep only their digits so the segment stays
        # purely numeric as required by the SI01 structured reference format.
        p1 = re.sub(r'\D', '', str(self.journal_id.id)) or '0'
        p2 = str(self.invoice_date.year)[-2:]
        reference_base = f"{p1}-{p2}-{p3}"

        # Calculate check digit
        digits = [int(d) for d in reference_base if d.isdigit()]
        weights = list(range(2, 14))[:len(digits)]
        weighted_sum = sum(d * w for d, w in zip(reversed(digits), weights))
        check_digit = 11 - (weighted_sum % 11)
        check_digit = 0 if check_digit in (10, 11) else check_digit
        return f"SI01 {reference_base}{check_digit}"
