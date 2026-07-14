# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from http import HTTPStatus

import odoo.http
from odoo.tests import tagged, get_db_name
from odoo.tests.common import new_test_user, Like
from odoo.tools import mute_logger
from odoo.tools.misc import submap
from odoo.addons.test_http.utils import HtmlTokenizer

from .test_common import TestHttpBase


@tagged('post_install', '-at_install')
class TestHttpModels(TestHttpBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.jackoneill = new_test_user(cls.env, 'jackoneill', context={'lang': 'en_US'})

    def setUp(self):
        super().setUp()
        self.authenticate('jackoneill', 'jackoneill')

    def test_models0_galaxy_ok(self):
        milky_way = self.env.ref('test_http.milky_way')
        earth = self.env.ref('test_http.earth')
        abydos = self.env.ref('test_http.abydos')
        dakara = self.env.ref('test_http.dakara')

        res = self.url_open(f"/test_http/{milky_way.id}")

        self.assertEqual(res.status_code, 200)
        # ids are uuids, so the rendered hrefs and designations must be
        # derived from the actual records rather than hardcoded int ids.
        expected_items = ''.join(
            f'<li><a href="/test_http/{milky_way.id}/{gate.id}">'
            f'{gate.name} ({gate.sgc_designation})</a></li>'
            for gate in (earth, abydos, dakara)
        )
        self.assertEqual(
            HtmlTokenizer.tokenize(res.text),
            HtmlTokenizer.tokenize(f'''\
                <p>Milky Way</p>
                <ul>
                    {expected_items}
                </ul>
                ''')
            )

    @mute_logger('odoo.http')
    def test_models1_galaxy_ko(self):
        # ids are uuids; use a well-formed but non-existent uuid
        res = self.url_open("/test_http/00000000-0000-0000-0000-000000000404")  # unknown galaxy
        self.assertEqual(res.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertIn('The Ancients did not settle there.', res.text)

    def test_models2_stargate_ok(self):
        milky_way = self.env.ref('test_http.milky_way')
        earth = self.env.ref('test_http.earth')

        res = self.url_open(f'/test_http/{milky_way.id}/{earth.id}')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            HtmlTokenizer.tokenize(res.text),
            HtmlTokenizer.tokenize(f'''\
                <dl>
                    <dt>name</dt><dd>Earth</dd>
                    <dt>address</dt><dd>sq5Abt</dd>
                    <dt>sgc_designation</dt><dd>{earth.sgc_designation}</dd>
                </dl>
            ''')
        )

    def test_models3_stargate_ko(self):
        milky_way = self.env.ref('test_http.milky_way')
        with self.assertLogs("odoo.http", level="WARNING") as logs:
            # ids are uuids; use a well-formed but non-existent uuid
            res = self.url_open(f'/test_http/{milky_way.id}/00000000-0000-0000-0000-000000009999')  # unknown gate
        self.assertEqual(res.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertIn("The goauld destroyed the gate", res.text)
        self.assertEqual(logs.output, ["WARNING:odoo.http:The goauld destroyed the gate"])

    def test_models4_stargate_setname(self):
        milky_way = self.env.ref('test_http.milky_way')


        milky_way.invalidate_recordset()
        res = self.url_open(f'/test_http/{milky_way.id}/setname?readonly=0', {
            'name': "Wilky May",
            'csrf_token': odoo.http.Request.csrf_token(self),
        })
        res.raise_for_status()

        milky_way.invalidate_recordset()
        self.assertEqual(milky_way.name, "Wilky May")

    def test_models5_stargate_setname_readonly(self):
        milky_way = self.env.ref('test_http.milky_way')

        self.assertEqual(milky_way.name, "Milky Way")

        with self.assertLogs('odoo.http', 'WARNING') as capture_http,\
             self.assertLogs('odoo.sql_db', 'WARNING') as capture_sql_db:
            res = self.url_open(f'/test_http/{milky_way.id}/setname?readonly=1', {
                'name': "Wilky May",
                'csrf_token': odoo.http.Request.csrf_token(self),
            })
            res.raise_for_status()

        milky_way.invalidate_recordset()
        self.assertEqual(milky_way.name, "Wilky May")
        self.assertEqual(capture_http.output, [
            Like("...cannot execute UPDATE in a read-only transaction, retrying with a read/write cursor..."),
        ])
        self.assertEqual(
            # capture_sql_db.ouput contains the full Stack info, we don't want it
            [rec.msg % rec.args for rec in capture_sql_db.records],
            [Like('bad query:...UPDATE "test_http_galaxy"...ERROR: cannot execute UPDATE in a read-only transaction')],
        )

    def test_models5_max_upload_too_large(self):
        res = self.url_open('/test_http/1/setname', {
            'name': "too much data" * 1000  # 1.3kB
        })
        self.assertEqual(res.status_code, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)

    def test_models6_rpc_path_poisoning(self):
        with self.assertLogs('werkzeug', logging.INFO) as capture:
            with mute_logger('odoo.addons.rpc.controllers.xmlrpc'):
                self.xmlrpc_object.execute_kw(
                    # ids are uuids; the stdlib xmlrpc client cannot marshal
                    # UUID objects, so pass their string form
                    get_db_name(), str(self.jackoneill.id), 'jackoneill',
                   'res.users', 'read', [str(self.jackoneill.id), ['login']]
                )
            res = self.url_open('/test_http/wsgi_environ')
            res.raise_for_status()

        self.assertEqual(capture.output, [
            Like('..."POST /xmlrpc/2/object#res.users.read HTTP/...'),
            Like('..."GET /test_http/wsgi_environ HTTP/...'),
        ], "there must be two requests, the first with a fragment, the second without")

        environ = {
            "PATH_INFO": "/test_http/wsgi_environ",
            "QUERY_STRING": "",
            "REQUEST_URI": "/test_http/wsgi_environ",
            "RAW_URI": "/test_http/wsgi_environ",
        }
        self.assertEqual(
            submap(res.json(), environ.keys()),
            environ,
            "the fragment must not leak in the next request")
        self.assertNotIn(
            '#res.users/read',
            res.text,
            "the fragment must not leak in the next request")
