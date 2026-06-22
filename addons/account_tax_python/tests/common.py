import json

from itertools import count

from odoo.addons.account.tests.test_tax import TestTaxCommon


class TestTaxCommonAccountTaxPython(TestTaxCommon):

    def _jsonify_tax(self, tax):
        values = super()._jsonify_tax(tax)
        values['formula_decoded_info'] = tax.formula_decoded_info
        return values

    def _run_js_tests(self):
        # EXTENDS 'account'
        # The jsonified test payload embeds record ids (taxes, products, uoms,
        # companies, ...) which are uuid primary keys. uuid.UUID is not JSON
        # serializable by default, so stringify them; the JS side compares ids
        # as opaque values, so string ids round-trip consistently.
        if not self.js_tests:
            return

        self.env['ir.config_parameter'].set_param(
            'account.tests_shared_js_python',
            json.dumps(
                [test for test, _expected_values, _assert_function in self.js_tests],
                default=str,
            ),
        )

        self.start_tour('/account/init_tests_shared_js_python', 'tests_shared_js_python', login=self.env.user.login)
        results = json.loads(self.env['ir.config_parameter'].get_param('account.tests_shared_js_python', '[]'))

        self.assertEqual(len(results), len(self.js_tests))
        for index, (js_test, expected_values, assert_function), r in zip(count(1), self.js_tests, results):
            js_test.update(r)
            with self.subTest(test=js_test['test'], index=index):
                assert_function(js_test, expected_values)

    def assert_python_taxes_computation(
        self,
        formula,
        price_unit,
        expected_values,
        product_values=None,
        product_uom_values=None,
        price_include_override='tax_excluded',
    ):
        tax = self.python_tax(formula, price_include_override=price_include_override)
        if product_values:
            product = self.env['product.product'].create({
                'name': "assert_python_taxes_computation",
                **product_values,
            })
        else:
            product = None
        if product_uom_values:
            uom = self.env['uom.uom'].create({
                'name': "assert_python_taxes_computation",
                'relative_uom_id': self.env.ref('uom.product_uom_unit').id,
                **product_uom_values,
            })
        else:
            uom = None
        return self.assert_taxes_computation(tax, price_unit, expected_values, product=product, product_uom=uom)
