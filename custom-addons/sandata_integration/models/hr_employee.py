# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions
# Copyright (C) 2022 (http://www.bistasolutions.com)
#
##############################################################################

import logging
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from cryptography.fernet import Fernet
# import cryptocode
import os.path


_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    employee_uuid = fields.Char(string="Employee UUID",
                        copy=False)
    employee_ssn = fields.Char(string="SSN Number",
                        copy=False)
    firstname = fields.Char(string="First Name", tracking=1)
    lastname = fields.Char(string="Last Name", tracking=1)
    is_need_to_update = fields.Boolean(string="Is Need To Update",
                                       copy=False)

    def generate_key(self):
        """
        Generates a key and save it into a file
        """
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    def load_key(self):
        """
        Load the previously generated key
        """
        return open("secret.key", "rb").read()

    def encrypt_message(self, message):
        """
        Encrypts a message
        """
        key = self.load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)
        return encrypted_message

    @api.model
    def create(self, vals):
        if "employee_ssn" in vals and vals.get('employee_ssn'):
            if len(vals.get('employee_ssn')) == 5:
                file_exists = os.path.exists('secret.key')
                if file_exists:
                    encrypt_msg = self.encrypt_message(vals["employee_ssn"])
                    vals['employee_ssn'] = encrypt_msg
                else:
                    self.generate_key()
                    encrypt_msg = self.encrypt_message(vals["employee_ssn"])
                    vals['employee_ssn'] = encrypt_msg
            else:
                raise ValidationError(_('Please Enter Last Five Digit of SSN Number'))
            # encoded = cryptocode.encrypt(vals["employee_ssn"], "mypassword")
            # vals['employee_ssn'] = encoded
        new_record = super().create(vals)
        return new_record

    def write(self, vals):
        if "employee_ssn" in vals:
            if len(vals.get('employee_ssn')) == 5:
                file_exists = os.path.exists('secret.key')
                if file_exists:
                    encrypt_msg = self.encrypt_message(vals["employee_ssn"])
                    vals['employee_ssn'] = encrypt_msg
                else:
                    self.generate_key()
                    encrypt_msg = self.encrypt_message(vals["employee_ssn"])
                    vals['employee_ssn'] = encrypt_msg
            else:
                raise ValidationError(_('Please Enter Last Five Digit of SSN Number'))
            # encoded = cryptocode.encrypt(vals["employee_ssn"], "mypassword")
            # vals['employee_ssn'] = encoded
        res = super().write(vals)
        return res


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('employee_ssn')
    def _check_employee_ssn_unique(self):
        employee_ssn_counts = self.search_count([('employee_ssn', '=', self.employee_ssn),
                                                 ('company_id', '=', self.env.company.id),
                                                 ('id', '!=', self.id)])
        if employee_ssn_counts > 0:
            raise ValidationError(_("Employee SSN already exists!"))

    def write(self, vals):
        if vals.get('work_email') or vals.get('firstname') or vals.get('lastname'):
            vals.update({'is_need_to_update': True})
        return super(HrEmployee, self).write(vals)


