# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import logging
import base64
import requests
import json
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from socket import gaierror, timeout


_logger = logging.getLogger(__name__)


class SanDataConfiguration(models.Model):
    _name = "sandata.configuration"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)
    mode = fields.Selection(string="Mode",
                            selection=[('disabled', "Disabled"), ('enabled', "Enabled"), ('test', "Test Mode")],
                            default='disabled', required=True, copy=False)
    state = fields.Selection(string="Status", selection=[('draft', "Not Confirm"), ('done', "Confirm")],
                              default='draft', required=True, copy=False)
    company_id = fields.Many2one(string="Company", comodel_name='res.company', default=lambda self: self.env.company.id,
                                 required=True)
    authorize_account = fields.Char(string="Account")
    authorize_provider = fields.Char(string="Provider ID", groups='base.group_system')
    authorize_user_id = fields.Char(string="User ID", groups='base.group_system')
    authorize_pass = fields.Char(string="Password")
    test_employee_url = fields.Char(string="Test Employee URL")
    test_client_url = fields.Char(string="Test Client URL")
    test_visit_url = fields.Char(string="Test Visit URL")
    prod_employee_url = fields.Char(string="Production Employee URL")
    prod_client_url = fields.Char(string="Production Client URL")
    prod_visit_url = fields.Char(string="Production Visit URL")
    test_get_employee_url = fields.Char(string="Test Get Employee URL")
    test_get_client_url = fields.Char(string="Test Get Client URL")
    test_get_visit_url = fields.Char(string="Test Get Visit URL")
    prod_get_employee_url = fields.Char(string="Production Get Employee URL")
    prod_get_client_url = fields.Char(string="Production Get Client URL")
    prod_get_visit_url = fields.Char(string="Production Get Visit URL")

    def set_draft(self):
        self.write({'state': 'draft'})
        return True

    def button_confirm_login(self):
        for server in self:
            try:
                # connection = server.connect()
                simple_string = server.authorize_user_id + ":" + server.authorize_pass
                simple_string_bytes = simple_string.encode("ascii")
                base64_bytes = base64.b64encode(simple_string_bytes)
                base64_string = base64_bytes.decode("ascii")
                resp = False
                status = False
                url_test = ''
                if server.mode == 'test':
                    url_test = server.test_get_visit_url + '?uuid='
                    resp = requests.get(url=url_test, data=[], params={}, headers={'Content-Type': 'application/json', 'Account': server.authorize_account, 'Authorization': 'Basic ' + base64_string})
                if server.mode == 'enabled':
                    url_test = server.prod_get_visit_url + '?uuid='
                    resp = requests.get(
                        url=url_test, data=[],
                        params={}, headers={'Content-Type': 'application/json', 'Account': server.authorize_account,
                                            'Authorization': 'Basic ' + base64_string})
                if resp:
                    status = resp.status_code
                if status == 200:
                    server.write({'state': 'done'})
                else:
                    to_compare = json.loads(resp.text)
                    if to_compare.get('error'):
                        raise Warning(to_compare.get('error'))
            except requests.exceptions.ConnectionError:
                _logger.exception("unable to reach endpoint at %s", url_test)
                raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
            except (OSError, Exception) as err:
                # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
                raise UserError(_("Connection test failed: %s", tools.ustr(err)))
            except (gaierror, timeout,) as e:
                raise UserError(_("No response received. Check server information.\n %s", tools.ustr(e)))
        return True

