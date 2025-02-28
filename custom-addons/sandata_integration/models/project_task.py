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
import odoo
import pytz
import threading
import phonenumbers
import logging
# import cryptocode
import os.path
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError, AccessError
from socket import gaierror, timeout
# from uszipcode import SearchEngine
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from cryptography.fernet import Fernet

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def open_create_attendance_wizard(self):
        form_view_id = self.env.ref('sandata_integration.wizard_create_attendance_form_view').id
        if form_view_id:
            return {
                    'name': _('Create Attendance Wizard'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'views': [
                            (form_view_id, 'form')],
                    'view_id': form_view_id,
                    'res_model': 'wizard.create.attendance',
                    'context': {'default_partner_id': self.partner_id and\
                                self.partner_id.id,
                                'tasks': self.id,
                                'from_main_task': True}
                    }

    def prepare_sandata_headers(self, sandata_config_id):
        simple_string = sandata_config_id.authorize_user_id + ":" + sandata_config_id.authorize_pass
        simple_string_bytes = simple_string.encode("ascii")
        base64_bytes = base64.b64encode(simple_string_bytes)
        base64_string = base64_bytes.decode("ascii")
        return {'Content-Type': 'application/json',
                'Account': sandata_config_id.authorize_account,
                'Authorization': 'Basic ' + base64_string}

    def prepare_sandata_provider(self, sandata_config_id):
        return {"ProviderID": sandata_config_id.authorize_provider,
                "ProviderQualifier": "MedicaidID"}

    def create_sandata_log(self, err, record):
        try:
            ct = threading.current_thread()
            ct_db = getattr(ct, 'dbname', None)
            dbname = tools.config['log_db'] if tools.config['log_db'] and tools.config['log_db'] != '%d' else ct_db
            if not dbname:
                return
            with odoo.sql_db.db_connect(dbname).cursor() as cr:
                conn = cr._cnx
                partner_id = self.env['res.users'].sudo().browse(self._context.get('uid')).partner_id
                cr.execute(""" INSERT INTO mail_message(create_date, create_uid, author_id, body, is_internal, message_id, record_name, subtype_id, model, res_id, subject, message_type)
                                            VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                                        """, (
                self._context.get('uid'), partner_id.id, tools.ustr(err), False, tools.generate_tracking_message_id('dummy-generate'),
                False, self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment'), 'project.task', record.id,
                'Sandata', 'comment'))
                cr.commit();
                id = cr.fetchone()[0]
        except (OSError, Exception) as err:
            raise ValidationError(_("%s", tools.ustr(err)))
        return True

    def trim_before_space(self, s):
        # Find the position of the first space
        space_index = s.find(' ')
        if space_index == -1:
            return s
        return s[space_index + 1:]

    def process_phone_number(self, s):
        cleaned_string = s.replace('-', '')
        if len(cleaned_string) == 10:
            return cleaned_string
        else:
            return "1234567890"

    def client_sandata_create_edit(self, record, via_atten_line_id, client_url, employee_url, url, attendace_type, headers, provider, get_client_url, sandata_mode):
        self.env['ks_project_task.ks_logger'].create({
            'name': 'client_sandata_create_edit',
            'update_data': False,
            'date': fields.datetime.now(),
            'response': "to_compare",
            'data_file': 'NULL'
        })
        sequance_data = self.create_squance()
        sequance = sequance_data.get('sequance')
        date_format = sequance_data.get('date_format')
        formatter = phonenumbers.AsYouTypeFormatter("en")
        formated_phone_number = ''
        if record.partner_id.phone:
            phone_number = self.trim_before_space(record.partner_id.phone)
            formated_phone_number = self.process_phone_number(phone_number)
        elif record.partner_id.mobile:
            phone_number = self.trim_before_space(record.partner_id.mobile)
            formated_phone_number = self.process_phone_number(phone_number)
        else:
            formated_phone_number = '1234567890'

        client_data = [
            {
                "ProviderIdentification": provider,
                "ClientQualifier": "ClientCustomID",
                "ClientIdentifier": record.partner_id.ma_number, #"9876543210",
                "ClientFirstName": record.partner_id.firstname, #"Test",
                "ClientLastName": record.partner_id.lastname,#"Client",
                "ClientMedicaidID": record.partner_id.ma_number,#"9876543210",
                "SequenceID": sequance,
                "ClientTimezone": "US/Eastern",
                "ClientCustomID": record.partner_id.ma_number, #"9999999999",
                "ClientPayerInformation": [
                    {
                        "PayerID": record.partner_id.payer, #"PAAHPH",
                        "PayerProgram": record.partner_id.payer_program, #"PHC",
                        "ProcedureCode": record.sale_line_id.product_id.procedure_code.name,
                        "Modifier1": record.sale_line_id.product_id.modifier_1.modifier_1 if record.sale_line_id.product_id.modifier_1 else "",
                        "Modifier2": record.sale_line_id.product_id.modifier_2.modifier_2 if record.sale_line_id.product_id.modifier_2 else "",
                        "Modifier3": record.sale_line_id.product_id.modifier_3.modifier_3 if record.sale_line_id.product_id.modifier_3 else "",
                        "Modifier4": record.sale_line_id.product_id.modifier_4.modifier_4 if record.sale_line_id.product_id.modifier_4 else "",
                        "ClientStatus": "02",
                    }
                ],
                "ClientAddress": [
                    {
                        "ClientAddressType": "Home",
                        "ClientAddressIsPrimary": True,
                        "ClientAddressLine1": record.partner_id.street,#"36 West 5th Street",
                        "ClientAddressLine2": record.partner_id.street2, #"10th Floor",
                        "ClientCounty": record.partner_id.county_id.name, #"Kings",
                        "ClientCity": record.partner_id.city,#"Manhattan",
                        "ClientState": record.partner_id.state_id.code, #"NY",
                        "ClientZip": record.partner_id.zip #"10017",
                    }
                ],
                "ClientPhone": [
                    {
                        "ClientPhoneType": "Home",
                        "ClientPhone":  formated_phone_number #"1234567890" #
                    }
                ],
            }
        ]
        try:
            resp = requests.post(url=client_url, data=json.dumps(client_data), params={}, headers=headers)
            _logger.info("+++++++++++++++  CLIENT DATA SEND  ++++++++++++++", resp.status_code)
            status = resp.status_code
            if status == 403:
                raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
            to_compare = json.loads(resp.text)
            self.env['ks_project_task.ks_logger'].create({
                'name': 'Client',
                'update_data': False,
                'date': fields.datetime.now(),
                'response': to_compare,
                'data_file': client_data
            })
            if status == 200:
                if to_compare.get('status') == 'FAILED':
                    if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                        msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                        raise Warning(msg)
                if to_compare.get('status') == 'SUCCESS':
                    resp = requests.get(url=get_client_url,
                                        data=[], params={'uuid': to_compare.get('id')}, headers=headers)
                    to_compare = json.loads(resp.text)
                    if to_compare.get('status') == 'SUCCESS':
                        record.partner_id.partner_uuid = to_compare.get('id')
                        record.partner_id.is_need_to_update = False
                        if sandata_mode == 'test':
                            self.create_sandata_log(to_compare.get('messageSummary'), record)
                    if to_compare.get('status') == 'FAILED':
                        if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                            msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                            raise Warning(msg)
            else:
                msg = to_compare.get('error') or ''
                msg = msg + " " + to_compare.get('message') or ''
                raise Warning(msg)
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", client_url)
            self.create_sandata_log("Connection Error: " + _("Could not establish the connection to the API."), record)
            raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            self.create_sandata_log(err, record)
            raise ValidationError(_("%s", tools.ustr(err)))
        except (gaierror, timeout,) as e:
            self.create_sandata_log(e, record)
            raise UserError(_("No response received. Check server information.\n %s", tools.ustr(e)))
        return True

    def get_employee_ssn(self, record, employee_id):
        try:
            key = employee_id.load_key()
            f = Fernet(key)
            ssn_byte = bytes(employee_id.employee_ssn, encoding='utf8')
            decrypted_message = f.decrypt(ssn_byte)
            return decrypted_message.decode()
        except Exception as e:
            raise ValidationError(_("Error during decryption SSN :", e))

    def employee_sandata_create_edit(self, record, via_atten_line_id, client_url, employee_url, url, attendace_type, headers, provider, get_employee_url, sandata_mode):
        self.env['ks_project_task.ks_logger'].create({
            'name': 'employee_sandata_create_edit',
            'update_data': False,
            'date': fields.datetime.now(),
            'response': "to_compare",
            'data_file': 'Null'
        })
        sequance_data = self.create_squance()
        sequance = sequance_data.get('sequance')
        date_format = sequance_data.get('date_format')
        # employee_ssn = self.get_employee_ssn(record, via_atten_line_id.employee_id)
        employee_ssn = via_atten_line_id.employee_id.employee_ssn_temp_base
        if len(employee_ssn) != 5:
            employee_ssn = '{:05}'.format(int(employee_ssn))
        employee_identifier = '0000' + employee_ssn
        employee_data = [{
            "ProviderIdentification": provider,
            "EmployeeQualifier": "EmployeeCustomID",
            "EmployeeIdentifier": employee_identifier, # "000012345"
            "SequenceID": sequance,
            "EmployeeLastName": via_atten_line_id.employee_id.lastname, #"Employee",
            "EmployeeFirstName": via_atten_line_id.employee_id.firstname, #"Test",
            "EmployeeEmail": via_atten_line_id.employee_id.work_email,# "dummy@sandata.com",# #
            "EmployeeSSN": employee_identifier # "000012345"
        }]
        try:
            resp = requests.post(url=employee_url, data=json.dumps(employee_data), params={}, headers=headers)
            status = resp.status_code
            if status == 403:
                raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
            to_compare = json.loads(resp.text)
            self.env['ks_project_task.ks_logger'].create({
                'name': 'Employee',
                'update_data': False,
                'date': fields.datetime.now(),
                'response': to_compare,
                'data_file': employee_data
            })
            if status == 200:
                if to_compare.get('status') == 'FAILED':
                    if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                        msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                        raise Warning(msg)
                if to_compare.get('status') == 'SUCCESS':
                    resp = requests.get(url=get_employee_url,
                                        data=[], params={'uuid': to_compare.get('id')}, headers=headers)
                    to_compare = json.loads(resp.text)
                    if to_compare.get('status') == 'SUCCESS':
                        via_atten_line_id.employee_id.sudo().employee_uuid = to_compare.get('id')
                        via_atten_line_id.employee_id.sudo().is_need_to_update = False
                        if sandata_mode == 'test':
                            self.create_sandata_log(to_compare.get('messageSummary'), record)
                    if to_compare.get('status') == 'FAILED':
                        if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                            msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                            raise Warning(msg)
            else:
                msg = to_compare.get('error') or ''
                msg = msg + " " + to_compare.get('message') or ''
                raise Warning(msg)
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", employee_url)
            self.create_sandata_log("Connection Error: " + _("Could not establish the connection to the API."), record)
            raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            self.create_sandata_log(err, record)
            raise ValidationError(_("%s", tools.ustr(err)))
        except (gaierror, timeout,) as e:
            self.create_sandata_log(e, record)
            raise UserError(_("No response received. Check server information.\n %s", tools.ustr(e)))
        return True

    def create_squance(self):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        # est = pytz.timezone('US/Eastern')
        medication_date_utc = False
        if self.env.context.get('kwargs', False) and self.env.context.get('kwargs').get('check_in_time'):
            medication_date_utc = datetime.strftime(pytz.utc.localize(
                datetime.strptime(self.env.context.get('kwargs').get('check_in_time'),
                                  DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local), "%Y-%m-%d %H:%M:%S")
            medication_date_utc = datetime.strptime(medication_date_utc, "%Y-%m-%d %H:%M:%S")
        elif self.env.context.get('kwargs', False) and self.env.context.get('kwargs').get('check_out_time'):
            medication_date_utc = datetime.strftime(pytz.utc.localize(
                datetime.strptime(self.env.context.get('kwargs').get('check_out_time'),
                                  DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local), "%Y-%m-%d %H:%M:%S")
            medication_date_utc = datetime.strptime(medication_date_utc, "%Y-%m-%d %H:%M:%S")
        else:
            medication_date_utc = datetime.strftime(pytz.utc.localize(
                datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local), "%Y-%m-%d %H:%M:%S")
            medication_date_utc = datetime.strptime(medication_date_utc, "%Y-%m-%d %H:%M:%S") - timedelta(days=1)
        sequance_id = str(medication_date_utc).replace(" ", "").replace("-", "").replace(":", "")
        date_format = str(medication_date_utc).replace(" ", "T") + 'Z'
        return {'sequance': sequance_id, 'date_format': date_format}

    def create_edit_sandata_record(self, record, via_atten_line_id, client_url, employee_url, url, attendace_type, headers, provider, get_client_url, get_employee_url, get_visit_url, sandata_mode, call_details=True, attendance_update=None):
        if not record.partner_id.partner_uuid or record.partner_id.is_need_to_update:
            client_data = self.client_sandata_create_edit(record, via_atten_line_id, client_url,
                                                          employee_url, url, attendace_type,
                                                          headers, provider, get_client_url, sandata_mode)
        if not via_atten_line_id.employee_id.employee_uuid or via_atten_line_id.employee_id.is_need_to_update:
            employee_data = self.employee_sandata_create_edit(record, via_atten_line_id, client_url,
                                                              employee_url, url, attendace_type,
                                                              headers, provider, get_employee_url, sandata_mode)
        self.env['ks_project_task.ks_logger'].create({
            'name': 'create_edit_sandata_record',
            'update_data': False,
            'date': fields.datetime.now(),
            'response': "to_compare",
            'data_file': "Null"
        })
        try:
            sequance_data = self.create_squance()
            sequance_id = sequance_data.get('sequance')
            date_format = sequance_data.get('date_format')
            adj_in_date = ""
            adj_out_date = ""
            if attendance_update and attendance_update.update_visit:
                adj_in_date = str(attendance_update.adj_in_date).replace(" ", "T") + 'Z'
                adj_out_date = str(attendance_update.adj_out_date).replace(" ", "T") + 'Z'
            if record.partner_id.partner_uuid and via_atten_line_id.employee_id.employee_uuid:
                employee_ssn = via_atten_line_id.employee_id.employee_ssn_temp_base
                # employee_ssn = self.get_employee_ssn(record,via_atten_line_id.employee_id)
                if len(employee_ssn) != 5:
                    employee_ssn = '{:05}'.format(int(employee_ssn))
                employee_identifier = '0000' + employee_ssn
                data = [{"ProviderIdentification": provider,
                         "VisitOtherID": str(int(via_atten_line_id.id)),
                         "SequenceID": sequance_id,  # YYYYMMDDHHMMSS formate sequence
                         "EmployeeQualifier": "EmployeeCustomID",
                         "EmployeeIdentifier": employee_identifier, #"000012345",
                         "ClientIDQualifier": "ClientCustomID",
                         "ClientIdentifier": record.partner_id.ma_number, #"9876543210",
                         "ClientID": record.partner_id.ma_number, #"9876543210",
                         "VisitCancelledIndicator": False,
                         "PayerID": record.partner_id.payer,  # "PAAHPH",
                         "PayerProgram": record.partner_id.payer_program,  # "PHC",
                         "ProcedureCode": record.sale_line_id.product_id.procedure_code.name,
                         "Modifier1": record.sale_line_id.product_id.modifier_1.modifier_1 if record.sale_line_id.product_id.modifier_1 else "",
                         "Modifier2": record.sale_line_id.product_id.modifier_2.modifier_2 if record.sale_line_id.product_id.modifier_2 else "",
                         "Modifier3": record.sale_line_id.product_id.modifier_3.modifier_3 if record.sale_line_id.product_id.modifier_3 else "",
                         "Modifier4": record.sale_line_id.product_id.modifier_4.modifier_4 if record.sale_line_id.product_id.modifier_4 else "", # T1019
                         "VisitTimeZone": "US/Eastern",
                         "BillVisit": True
                         # "Calls": [
                         #     {
                         #         "CallExternalID": via_atten_line_id.id, #"123456789",
                         #         "CallDateTime": date_format,  # "2019-07-28T16:02:26Z", #
                         #         "CallAssignment": "Time In" if attendace_type == 'check_in' else "Time Out",
                         #         "VisitLocationType": '1',
                         #         # "CallType": "Manual",
                         #         "CallType": record.sale_line_id.product_id.call_type if record.sale_line_id.product_id.call_type else "Manual",
                         #         "ProcedureCode": record.sale_line_id.product_id.procedure_code.name,
                         #         'MobileLogin': record.sale_line_id.product_id.mobile_login if record.sale_line_id.product_id.mobile_login else "",
                         #         "ClientIdentifierOnCall": "111111111",
                         #         # "MobileLogin": '',
                         #         "CallLatitude": via_atten_line_id.check_in_latitude if attendace_type == 'check_in' else via_atten_line_id.check_out_latitude,
                         #         "CallLongitude": via_atten_line_id.check_in_longitude if attendace_type == 'check_in' else via_atten_line_id.check_out_longitude,
                         #         # "Location": "123",
                         #     }
                         # ]
                         }]
                if attendance_update and attendance_update.update_visit and attendance_update.adj_in_date:
                    data[0].update({
                         "AdjInDateTime": adj_in_date if attendance_update and attendance_update.update_visit and attendance_update.adj_in_date else ""
                    })
                if attendance_update and attendance_update.update_visit and attendance_update.adj_out_date:
                    data[0].update({
                         "AdjOutDateTime": adj_out_date if attendance_update and attendance_update.update_visit and attendance_update.adj_out_date else ""
                    })
                if attendance_update and attendance_update.client_verified_times:
                    data[0].update({
                        "ClientVerifiedTimes": True
                    })
                if attendance_update and attendance_update.client_signature:
                    data[0].update({
                        "ClientSignatureAvailable": True
                    })
                if call_details:
                    data[0].update({"Calls": [{
                        "CallExternalID": via_atten_line_id.id, #"123456789",
                        "CallDateTime": date_format,  # "2019-07-28T16:02:26Z", #
                        "CallAssignment": "Time In" if attendace_type == 'check_in' else "Time Out",
                        "VisitLocationType": '1',
                        # "CallType": "Manual",
                        "CallType": record.sale_line_id.product_id.call_type if record.sale_line_id.product_id.call_type else "Manual",
                        "ProcedureCode": record.sale_line_id.product_id.procedure_code.name,
                        'MobileLogin': record.sale_line_id.product_id.mobile_login if record.sale_line_id.product_id.mobile_login else "",
                        "ClientIdentifierOnCall": "111111111",
                        # "MobileLogin": '',
                        "CallLatitude": via_atten_line_id.check_in_latitude if attendace_type == 'check_in' else via_atten_line_id.check_out_latitude,
                        "CallLongitude": via_atten_line_id.check_in_longitude if attendace_type == 'check_in' else via_atten_line_id.check_out_longitude,
                        # "Location": "123",
                    }]})
                if attendance_update and attendance_update.exception_acknowledgement:
                    data[0].update({"VisitExceptionAcknowledgement": [{
                        "ExceptionID": str(attendance_update.exception_id),  # "12",
                        "ExceptionAcknowledged": True
                    }]})

                if attendance_update and attendance_update.update_visit:
                    data[0].update({"VisitChanges": [{
                        "SequenceID": sequance_id,  # "110",
                        # "ChangeMadeBy": via_atten_line_id.employee_id.work_email,  # "dummy@sandata.com",
                        "ChangeMadeBy": self.env.user.login,  # "dummy@sandata.com",
                        "ChangeDateTime": date_format,
                        "ReasonCode": attendance_update.reasoncode if attendance_update.reasoncode else "10",
                        "ChangeReasonMemo": attendance_update.reason_memo if attendance_update.reason_memo else "Employee Check Out",
                        # "ResolutionCode": "A"
                        "ResolutionCode": attendance_update.resolution_code if attendance_update.resolution_code else "A"
                    }]})

                # "Tasks": [
                #     {
                #         "TaskID": record.id,
                #         "TaskReading": "98.6",
                #         "TaskRefused": False
                #     }
                # ]
                if attendace_type == "check_out":
                    data[0].update({"VisitChanges": [{
                                 "SequenceID": sequance_id, #"110",
                                 # "ChangeMadeBy": via_atten_line_id.employee_id.work_email, #"dummy@sandata.com",
                                 "ChangeMadeBy": self.env.user.login, #"dummy@sandata.com",
                                 "ChangeDateTime": date_format,
                                 # "GroupCode": '',
                                 # "ReasonCode": "10",
                                 "ReasonCode": record.sale_line_id.product_id.reasoncode if record.sale_line_id.product_id.reasoncode else "10",
                                 "ChangeReasonMemo": "Employee Check Out",
                                 # "ResolutionCode": "A"
                                 "ResolutionCode": record.sale_line_id.product_id.resolution_code if record.sale_line_id.product_id.resolution_code else "A"
                             }]})
                resp = requests.post(url=url, data=json.dumps(data), params={}, headers=headers)
                status = resp.status_code
                if status == 403:
                    self.env['ks_project_task.ks_logger'].create({
                        'name': 'Could not establish the connection to the API.',
                        'update_data': True if attendace_type == "check_out" else False,
                        'date': fields.datetime.now(),
                        'response': 'to_compare',
                        'data_file': 'Null'
                    })
                    raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
                to_compare = json.loads(resp.text)
                self.env['ks_project_task.ks_logger'].create({
                    'name': 'Visitor',
                    'update_data': True if attendace_type == "check_out" else False,
                    'date': fields.datetime.now(),
                    'response': to_compare,
                    'data_file': data
                })
                if status == 200:
                    if to_compare.get('status') == 'FAILED':
                        if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                            msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                            raise Warning(msg)
                    if to_compare.get('status') == 'SUCCESS':
                        resp = requests.get(url=get_visit_url, data=[], params={'uuid': to_compare.get('id')}, headers=headers)
                        to_compare = json.loads(resp.text)
                        if to_compare.get('status') == 'SUCCESS' and sandata_mode == 'test':
                            self.create_sandata_log("All records updated successfully", record)
                        if to_compare.get('status') == 'FAILED':
                            # if to_compare.get('data')[0].get('ErrorCode') == -1021 and to_compare.get('data')[0].get('ErrorMessage') == 'Client not found':
                            #     client_data = self.client_sandata_create_edit(record, via_atten_line_id, client_url,
                            #                                                   employee_url, url, attendace_type,
                            #                                                   headers, provider, sequance_id)
                            #     if client_data:
                            #         self.create_edit_sandata_record(record, via_atten_line_id, client_url, employee_url, url, attendace_type, headers, provider)
                            # elif to_compare.get('data')[0].get('ErrorCode') == -1031 and to_compare.get('data')[0].get('ErrorMessage') == 'Worker not found':
                            #     employee_data = self.employee_sandata_create_edit(record, via_atten_line_id, client_url,
                            #                                                       employee_url, url, attendace_type,
                            #                                                       headers, provider, sequance_id)
                            #     if employee_data:
                            #         self.create_edit_sandata_record(record, via_atten_line_id, client_url, employee_url, url, attendace_type, headers, provider)
                            # else:
                            if to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail'):
                                msg = to_compare.get('data')[0].get('ErrorMessage') or to_compare.get('messageDetail')
                                raise Warning(msg)
                else:
                    msg = to_compare.get('error') or ''
                    msg = msg + " " + to_compare.get('message') or ''
                    raise Warning(msg)
        except requests.exceptions.ConnectionError:
            _logger.exception("unable to reach endpoint at %s", url)
            self.create_sandata_log("Connection Error: " + _("Could not establish the connection to the API."), record)
            raise ValidationError("Connection Error: " + _("Could not establish the connection to the API."))
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            self.create_sandata_log(err, record)
            raise ValidationError(_("%s", tools.ustr(err)))
        except (gaierror, timeout,) as e:
            self.create_sandata_log(e, record)
            raise UserError(_("No response received. Check server information.\n %s", tools.ustr(e)))
        return True

    def get_partner_lat_long(self, partner_id):
        return {'lat': partner_id.partner_latitude, 'lng': partner_id.partner_longitude}
    
    def timesheet_sign_in(self, kwargs=None):
        """
        :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
        """
        try:
            if self.env.context.get('from_note') or self.env.context.get('create_attendance') or \
                    self.env.context.get('from_delay_reason') or (self.project_id and not self.project_id.program_type or \
                                                              self.project_id.program_type not in ['ihcs', 
                                                                                                #    'ihcs_e',
                                                                                                   'ihcs_2_1',
                                                                                                   'ihcs_e',
                                                                                                   'companion', 'cps',
                                                                                                   'cpse']):
                project_task_obj = self.env['project.task']
                via_atten_line_obj = self.env['via.attendance.line']
                user = self.env.user
                company = self.env.company
                employee_id = self.env['hr.employee'].search([
                    ('user_id', '=', user.id),
                    ('company_id', '=', company.id)],
                    limit=1)
                # kwargs = self.env.context.get('kwargs')
                task_ids = False
                if self.project_id and self.project_id.program_type not in ['ihcs', 
                                                                            # 'ihcs_e', 
                                                                            'ihcs_2_1', 'ihcs_e',
                                                                            'companion', 'cps', 'cpse']:
                    task_ids = self
                else:
                    task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
                if self.env.context.get('create_attendance'):

                    lat_long = self.get_partner_lat_long(self.env.context.get('partner_id'))
                    if kwargs is None:
                        kwargs = lat_long
                    else:
                        kwargs.update(lat_long)
                    kwargs.update({'check_in_time': self.env.context.get('check_in_time')})
                if employee_id:
                    for record in task_ids:
                        # if not self.env.context.get('from_main_task') and record.partner_id.program_type and \
                        #         record.partner_id.program_type in ['ihcs', 'ihcs_e', 'ihcs_2_1', 'ihcs_e', 'companion']:
                        float_diff = 0.0
                        user_tz = self.env.user.tz or pytz.utc
                        local = pytz.timezone(user_tz)
                        current_time = datetime.now(local).strftime('%Y-%m-%d %H:%M:%S')
                        c_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                        if record.planned_date_begin and record.planned_date_end:
                            # if (record.planned_date_begin.date() < c_time.date()) and (record.planned_date_end.date() >= c_time.date()):
                            if not self.env.context.get('from_delay_reason'):

                                start_date = datetime.strftime(pytz.utc.localize(
                                    datetime.strptime(record.planned_date_begin.strftime("%Y-%m-%d %H:%M:%S"),
                                                      DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local), "%Y-%m-%d %H:%M:%S")
                                params = self.env['ir.config_parameter'].sudo()
                                delay_time = params.get_param('delay_time',
                                                              default=False)
                                if delay_time:
                                    time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(delay_time) * 60, 60))
                                    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                                    differance = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S') - start_date
                                    start_date = start_date + timedelta(days=differance.days, hours=int(str(time.split(':')[0])),
                                                                        minutes=int(str(time.split(':')[1])))
                                    if datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S') > start_date:
                                        diff = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S') - start_date
                                        vals = str(diff).split(':')
                                        t, hours = divmod(float(vals[0]), 24)
                                        t, minutes = divmod(float(vals[1]), 60)
                                        minutes = minutes / 60.0
                                        float_diff = hours+minutes
                            # else:
                            #     raise ValidationError(_("Check-in time must be between planned date"))
                        else:
                            raise ValidationError(_("Please Select Planned Date."))
                        if float_diff:
                            if kwargs is None:
                                kwargs = {}
                            kwargs.update({'delay_time': float_diff})
                            form_view_id = self.env.ref('sandata_integration.delay_reason_wizard_form_view').id
                            return {
                                'name': _('Delay Reason'),
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'delay.reason.wizard',
                                'view_id': form_view_id,
                                'type': 'ir.actions.act_window',
                                'target': 'new',
                                'context': {'kwargs': kwargs, 'tasks': self.env.context.get('tasks') or record.id}
                            }

                        via_line_ids = via_atten_line_obj.search([
                            ('employee_id', '=', employee_id.id),
                            ('check_out_time', '=', False),
                            ('company_id', '=', company.id),
                            ('task_id', '!=', False)], limit=1)
                        if via_line_ids:
                            raise ValidationError(_("""At a time you can Check-in in the one task only. Please checkout from %s task is %s.""", via_line_ids.task_id.project_id.name, via_line_ids.task_id.name))

                        check_in_time = False
                        is_manual = False
                        if kwargs.get('check_in_time'):
                            check_in_time = kwargs.get('check_in_time')
                            is_manual = True
                        else:
                            check_in_time = fields.Datetime.now()
                        via_atten_line_id = via_atten_line_obj.create({
                            'date': fields.Date.today(),
                            'task_id': record.id,
                            'check_in_time': check_in_time,
                            'check_in_latitude': kwargs.get('lat'),
                            'check_in_longitude': kwargs.get('lng'),
                            'delay_time_differance': kwargs.get('delay_time') or 0.0,
                            'temperature': kwargs.get('temperature'),
                            'delay_reason': kwargs.get('delay_reason'),
                            'is_manual': is_manual,
                        })
                        if record.project_id and record.project_id.program_type and record.project_id.program_type in ['ihcs', 
                                                                                                                    #    'ihcs_e',
                                                                                             'ihcs_2_1', 'ihcs_e',
                                                                                             'companion', 'cps', 'cpse']:
                            sandata_config_id = self.env['sandata.configuration'].sudo().search([('state', '=', 'done'),
                                                                                    ('company_id', '=', self.env.company.id)], limit=1)
                            if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
                                headers = project_task_obj.prepare_sandata_headers(sandata_config_id)
                                provider = project_task_obj.prepare_sandata_provider(sandata_config_id)
                                if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
                                    project_task_obj.   create_edit_sandata_record(record, via_atten_line_id, sandata_config_id.prod_client_url, sandata_config_id.prod_employee_url, sandata_config_id.prod_visit_url, 'check_in', headers, provider, sandata_config_id.prod_get_client_url, sandata_config_id.prod_get_employee_url, sandata_config_id.prod_get_visit_url, sandata_config_id.mode)
                                if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
                                    project_task_obj.create_edit_sandata_record(record, via_atten_line_id, sandata_config_id.test_client_url, sandata_config_id.test_employee_url, sandata_config_id.test_visit_url,
                                                                                'check_in', headers, provider, sandata_config_id.test_get_client_url, sandata_config_id.test_get_employee_url, sandata_config_id.test_get_visit_url, sandata_config_id.mode)
                                # self.via_atten_line_id = via_atten_line_id.id
                            else:
                                raise ValidationError(_("""Please set Sandata Configuration"""))
                else:
                    raise ValidationError(_("Please Create Employee For Current User"))
            else:
                form_view_id = self.env.ref('bista_timesheet_attendance.attendance_confirm_message_wizard_form_view').id
                message_id = self.env['attendance.confirm.message'].search([], limit=1)
                return {
                    'name': _('Terms & Conditions'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'attendance.confirm.message.wizard',
                    'view_id': form_view_id,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {'default_msg_description': message_id.confirm_message, 'message_id': message_id.id,
                                'kwargs': kwargs, 'tasks': self.ids}
                }
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            # project_task_obj.create_sandata_log(err, task_ids)
            raise ValidationError(_("%s", tools.ustr(err)))
        return True

    def open_service_note_line(self, form_view_id, kwargs, ids):
        return {
            'name': _('Service Notes'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'via.service.note.wizard',
            'view_id': form_view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'kwargs': kwargs,
                        'tasks': ids}
        }

    def timesheet_sign_out(self, kwargs=None):
        """
        :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
        """
        try:
            if self.env.context.get('from_note'):
                if self.project_id and self.project_id.program_type not in ['ihcs', 
                                                                            # 'ihcs_e', 
                                                                            'ihcs_2_1', 'ihcs_e',
                                                                            'companion', 'cps', 'cpse']:
                    task_ids = self
                else:
                    if self.env.context.get('tasks'):
                        task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
                    else:
                        task_ids = self.env['project.task'].browse(self.env.context.get('params').get('id'))
                # task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
                via_atten_line_obj = self.env['via.attendance.line']
                analytic_line_obj = self.env['account.analytic.line']
                via_service_note_obj = self.env['via.service.note']
                user = self.env.user
                company = self.env.company
                employee_id = self.env['hr.employee'].search([
                                                ('user_id', '=', user.id),
                                                ('company_id', '=', company.id)], limit=1)
                if employee_id and task_ids:
                    worked_hours = 0.0
                    for record in task_ids:
                        user_tz = self.env.user.tz or pytz.utc
                        local = pytz.timezone(user_tz)
                        current_time = datetime.now(local).strftime('%Y-%m-%d %H:%M:%S')
                        c_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
                        # if (record.planned_date_begin.date() < c_time.date()) and (
                        #         record.planned_date_end.date() >= c_time.date()):
                        via_line_ids = via_atten_line_obj.search([
                                                ('employee_id', '=', employee_id.id),
                                                ('check_out_time', '=', False),
                                                ('task_id', '!=', record.id),
                                                ('task_id', '!=', False),
                                                ('company_id', '=', company.id)], limit=1)
                        if via_line_ids:
                            raise ValidationError(_("""Please Check-out from %s task first.""", via_line_ids.task_id.name))
                        sign_in_line = via_atten_line_obj.search([
                                                ('employee_id', '=', employee_id.id),
                                                ('company_id', '=', company.id),
                                                ('task_id', '=', record.id),
                                                ('check_out_time', '=', False)],
                                                limit=1, order='id desc')
                        #       self.env.context.get('check_out_time'))
                        if sign_in_line:
                            # if not kwargs.get('isp_data'):
                            #     raise ValidationError(_("""Please Enter Service Note Line."""))
                            if sign_in_line.is_manual:
                                if self.env.context.get('from_checkout'):
                                    if kwargs is None:
                                        kwargs = {}
                                        form_view_id = self.env.ref('sandata_integration.via_service_note_wizard_form_view').id
                                        if self.env.context.get('from_checkout'):
                                            kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
                                            task_id = self.env['project.task'].sudo().browse(self.ids)
                                            if record:
                                                if record[0].sale_line_id and record[0].sale_line_id.order_id.partner_id and \
                                                        record[0].sale_line_id.order_id.partner_id.isp_ids:
                                                    isp_ids = record[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
                                                        lambda isp: isp.product_id.id == record[0].sale_line_id.product_id.id).sorted(key=lambda r: r.id)
                                                    if isp_ids:
                                                        list_data = []
                                                        if isp_ids[-1].outcome_phrase:
                                                            list_data.append(
                                                                (0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
                                                                        'isp_id': isp_ids[-1].id
                                                                        }))
                                                        # if isp_ids[-1].reason_for_outcome:
                                                        #     list_data.append((0, 0, {
                                                        #         'outcome_phrase': isp_ids[-1].reason_for_outcome,
                                                        #         'isp_id': isp_ids[-1].id
                                                        #         }))
                                                        # if isp_ids[-1].outcome_statement:
                                                        #     list_data.append(
                                                        #         (0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
                                                        #                 'isp_id': isp_ids[-1].id
                                                        #                 }))
                                                        # if isp_ids[-1].actions_taken:
                                                        #     list_data.append(
                                                        #         (0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
                                                        #                 'isp_id': isp_ids[-1].id
                                                        #                 }))
                                                        # if isp_ids[-1].progress_status:
                                                        #     list_data.append(
                                                        #         (0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
                                                        #                 'isp_id': isp_ids[-1].id
                                                        #                 }))
                                                        return {
                                                            'name': _('Service Notes'),
                                                            'view_type': 'form',
                                                            'view_mode': 'form',
                                                            'res_model': 'via.service.note.wizard',
                                                            'view_id': form_view_id,
                                                            'type': 'ir.actions.act_window',
                                                            'target': 'new',
                                                            'context': {'kwargs': kwargs,
                                                                        'tasks': self.env.context.get('tasks'),
                                                                        'default_service_note_survey_ids': list_data}
                                                        }
                                                    else:
                                                        return self.open_service_note_line(form_view_id, kwargs,
                                                                                           self.env.context.get('tasks'))
                                                else:
                                                    return self.open_service_note_line(form_view_id, kwargs,
                                                                                       self.env.context.get('tasks'))
                                    sign_in_line.sudo().write({
                                        'check_out_time': kwargs.get('check_out_time'),
                                        'check_out_latitude': sign_in_line.check_in_latitude,
                                        'check_out_longitude': sign_in_line.check_in_longitude,
                                        # 'note': kwargs.get('note') or '',
                                        'is_checkout_done': True
                                    })
                                else:
                                    raise ValidationError(_("""Please do checkout from the manually"""))
                            if not sign_in_line.is_manual and not self.env.context.get('from_checkout'):
                                sign_in_line.sudo().write({'check_out_time': fields.Datetime.now(),
                                                    'check_out_latitude': kwargs.get('lat'),
                                                    'check_out_longitude': kwargs.get('lng'),
                                                    'note': kwargs.get('note') or ''
                                                    })
                            hours_spent = 0.0
                            if record.project_id and record.project_id.program_type and record.project_id.program_type not in ['support_brokering',
                                                                                                     'htts']:
                                duration = (sign_in_line.check_out_time - sign_in_line.check_in_time).total_seconds() / 3600
                                hours_spent = round(duration, 2)
                            analytic_line_id = analytic_line_obj.sudo().create({'date': sign_in_line.date,
                                                                                'employee_id': employee_id.id,
                                                                                'name': sign_in_line.description or '',
                                                                                'check_in_time': sign_in_line.check_in_time,
                                                                                'check_out_time': sign_in_line.check_out_time,
                                                                                'latitude_in': sign_in_line.check_in_latitude,
                                                                                'longitude_in': sign_in_line.check_in_longitude,
                                                                                'latitude_out': sign_in_line.check_out_latitude,
                                                                                'longitude_out': sign_in_line.check_out_longitude,
                                                                                'task_id': sign_in_line.task_id.id,
                                                                                'unit_amount': hours_spent,
                                                                                'program_type': record.project_id.program_type,
                                                                                # 'duration_unit_amount': hours_spent,
                                                                                # 'unit_amount_validate':  hours_spent,
                                                                                'is_so_line_edited': False,
                                                                                'product_uom_id': sign_in_line.task_id.sale_line_id.order_id.timesheet_encode_uom_id.id
                                                                                })
                            if kwargs.get('isp_data'):
                                for isp_data in kwargs.get('isp_data'):
                                    via_service_note_obj.sudo().create({'project_id': sign_in_line.task_id.project_id.id,
                                                                        'task_id': sign_in_line.task_id.id,
                                                                        'via_attendance_line_id': sign_in_line.id,
                                                                        'partner_id': sign_in_line.task_id.partner_id.id or False,
                                                                        'outcome_phrase': isp_data.get('outcome_phrase') or '',
                                                                        'reason_for_outcome': isp_data.get('reason_for_outcome') or '',
                                                                        'outcome_statement': isp_data.get('outcome_statement') or '',
                                                                        'actions_taken': isp_data.get('actions_taken') or '',
                                                                        'progress_status': isp_data.get('progress_status') or '',
                                                                        'survey_answer': isp_data.get('survey_answer') or '',
                                                                        'start_time': isp_data.get('start_time') or 0,
                                                                        'end_time': isp_data.get('end_time') or 0,
                                                                        'service_delivery_date': isp_data.get('service_delivery_date') or False,
                                                                        'description_of_activities': isp_data.get('note') or '',
                                                                        'note': isp_data.get('note') or '',
                                                                        'isp_id': isp_data.get('isp_id'),
                                                                        'employee_id': self.env.user.employee_id.id,
                                                                        'user_id': self.env.user.id,
                                                                        'account_analytic_line_id': analytic_line_id.id})
                            if record.project_id and record.project_id.program_type and record.project_id.program_type in ['ihcs', 
                                                                                                                        #    'ihcs_e',
                                                                                                 'ihcs_2_1', 'ihcs_e',
                                                                                                 'companion', 'cps', 'cpse']:
                                sandata_config_id = self.env['sandata.configuration'].sudo().search([('state', '=', 'done'),
                                                                                                     ('company_id', '=', self.env.company.id)], limit=1)
                                if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
                                    headers = self.prepare_sandata_headers(sandata_config_id)
                                    provider = self.prepare_sandata_provider(sandata_config_id)
                                    if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
                                        self.create_edit_sandata_record(record, sign_in_line, sandata_config_id.prod_client_url, sandata_config_id.prod_employee_url, sandata_config_id.prod_visit_url,
                                                                        'check_out', headers, provider, sandata_config_id.prod_get_employee_url, sandata_config_id.prod_get_visit_url, sandata_config_id.mode)
                                    if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
                                        self.create_edit_sandata_record(record, sign_in_line, sandata_config_id.test_client_url, sandata_config_id.test_employee_url, sandata_config_id.test_visit_url,
                                                                        'check_out', headers, provider, sandata_config_id.test_get_client_url, sandata_config_id.test_get_employee_url, sandata_config_id.test_get_visit_url, sandata_config_id.mode)
                                else:
                                    raise ValidationError(_("""Please set Sandata Configuration"""))
                        else:
                            raise ValidationError(_("""Please Check-in first."""))
                        # else:
                        #     raise ValidationError(_("Check-out time must be between planned date"))
                else:
                    raise ValidationError(_("Please Create Employee For Current User"))
            else:
                form_view_id = self.env.ref('sandata_integration.via_service_note_wizard_form_view').id
                if self.env.context.get('from_checkout'):
                    if kwargs is None:
                        kwargs = {}
                    kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
                    task_id = self.env['project.task'].sudo().browse(self.ids)
                    if not task_id:
                        if self.project_id and self.project_id.program_type not in ['ihcs', 'ihcs_e', 'ihcs_2_1',
                                                                                    # 'ihcs_e',
                                                                                    'companion', 'cps', 'cpse']:
                            task_id = self
                        else:
                            task_id = self.env['project.task'].browse(self.env.context.get('tasks'))
                    if task_id:
                        if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
                                task_id[0].sale_line_id.order_id.partner_id.isp_ids:
                            isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
                                lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(key=lambda r: r.id)
                            if isp_ids:
                                list_data = []
                                if isp_ids[-1].outcome_phrase:
                                    list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
                                                             'isp_id': isp_ids[-1].id
                                                             }))
                                # if isp_ids[-1].reason_for_outcome:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].outcome_statement:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].actions_taken:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].progress_status:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                return {
                                    'name': _('Service Notes'),
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'via.service.note.wizard',
                                    'view_id': form_view_id,
                                    'type': 'ir.actions.act_window',
                                    'target': 'new',
                                    'context': {'kwargs': kwargs,
                                                'tasks': self.env.context.get('tasks'),
                                                'default_service_note_survey_ids': list_data}
                                }
                            else:
                                return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
                        else:
                            return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
                else:
                    task_id = self.env['project.task'].sudo().browse(self.ids)
                    if task_id:
                        if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
                                task_id[0].sale_line_id.order_id.partner_id.isp_ids:
                            isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(key=lambda r: r.id)
                            if isp_ids:
                                list_data = []
                                if isp_ids[-1].outcome_phrase:
                                    list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
                                                             'isp_id': isp_ids[-1].id
                                                             }))
                                # if isp_ids[-1].reason_for_outcome:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].outcome_statement:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].actions_taken:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                # if isp_ids[-1].progress_status:
                                #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
                                #                              'isp_id': isp_ids[-1].id
                                #                              }))
                                return {
                                    'name': _('Service Notes'),
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'via.service.note.wizard',
                                    'view_id': form_view_id,
                                    'type': 'ir.actions.act_window',
                                    'target': 'new',
                                    'context': {'kwargs': kwargs,
                                                'tasks': self.ids,
                                                'default_service_note_survey_ids': list_data}
                                }
                            else:
                                return self.open_service_note_line(form_view_id, kwargs, self.ids)
                        else:
                            return self.open_service_note_line(form_view_id, kwargs, self.ids)
        except (OSError, Exception) as err:
            # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
            # self.create_sandata_log(err, task_ids)
            raise ValidationError(_("%s", tools.ustr(err)))
        return True

    # def create_data_in_api(self):
    #     sandata_config_id = self.env['sandata.configuration'].sudo().search([('state', '!=', 'disabled')], limit=1)
    #     if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id.authorize_pass:
    #         _string = "H8ALVNhv6fJL:gnn5Cb3ThyDr"
    #         sample_string_bytes = sample_string.encode("ascii")
    #
    #         base64_bytes = base64.b64encode(sample_string_bytes)
    #         base64_string = base64_bytes.decode("ascii")
    #
    #         authorizarion =
    #         if sandata_config_id.state == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
    #             pass
    #         if sandata_config_id.state == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
    #             pass
    #
    #
 # data = [{"ProviderIdentification": {"ProviderID": sandata_config_id.authorize_provider,
 #                                                        "ProviderQualifier": "MedicaidID"},
 #                             "VisitOtherID": "123456789",
 #                             "SequenceID": 111,
 #                             "EmployeeQualifier": "EmployeeCustomID",
 #                             "EmployeeOtherID": "999999999",
 #                             "EmployeeIdentifier": "999999999",
 #                             "GroupCode": '',
 #                             "ClientIDQualifier": "ClientCustomID",
 #                             "ClientID": "111111111",
 #                             "ClientOtherID": "111111111",
 #                             "VisitCancelledIndicator": False,
 #                             "PayerID": "PAABH",
 #                             "PayerProgram": "CHC",
 #                             "ProcedureCode": "T1000",
 #                             "Modifier1": '',
 #                             "Modifier2": '',
 #                             "Modifier3": '',
 #                             "Modifier4": '',
 #                             "VisitTimeZone": "US/Eastern",
 #                             "ScheduleStartTime": "2019-07-28T16:02:26Z",
 #                             "ScheduleEndTime": "2019-07-28T20:02:26Z",
 #                             "ContingencyPlan": "CP01",
 #                             "Reschedule": "No",
 #                             "AdjInDateTime": "2019-07-28T15:02:26Z",
 #                             "AdjOutDateTime": "2019-07-28T19:02:26Z",
 #                             "BillVisit": True,
 #                             "HoursToBill": 10,
 #                             "HoursToPay": 10,
 #                             "Memo": "This is a memo!",
 #                             "ClientVerifiedTimes": True,
 #                             "ClientVerifiedTasks": True,
 #                             "ClientVerifiedService": True,
 #                             "ClientSignatureAvailable": True,
 #                             "ClientVoiceRecording": True,
 #                             "Calls": [
 #                                 {
 #                                     "CallExternalID": "123456789",
 #                                     "CallDateTime": "2019-07-28T16:02:26Z",
 #                                     "CallAssignment": "Time In",
 #                                     "GroupCode": '',
 #                                     "CallType": "Other",
 #                                     "ProcedureCode": "T1000",
 #                                     "ClientIdentifierOnCall": "111111111",
 #                                     "MobileLogin": '',
 #                                     "CallLatitude": '',
 #                                     "CallLongitude": '',
 #                                     "Location": "123",
 #                                     "TelephonyPIN": 999999999,
 #                                     "OriginatingPhoneNumber": "9997779999"
 #                                 }
 #                             ],
 #                             "VisitExceptionAcknowledgement": [
 #                                 {
 #                                     "ExceptionID": "15",
 #                                     "ExceptionAcknowledged": False
 #                                 }
 #                             ],
 #                             "VisitChanges": [
 #                                 {
 #                                     "SequenceID": "110",
 #                                     "ChangeMadeBy": "dummy@sandata.com",
 #                                     "ChangeDateTime": "2019-07-25T18:45:00Z",
 #                                     "GroupCode": "",
 #                                     "ReasonCode": "10",
 #                                     "ChangeReasonMemo": "Change Reason Memo 999",
 #                                     "ResolutionCode": "A"
 #                                 }
 #                             ],
 #                             "Tasks": [
 #                                 {
 #                                     "TaskID": "321",
 #                                     "TaskReading": "98.6",
 #                                     "TaskRefused": False
 #                                 }
 #                             ]
 #                             }]




 # visit data


 # visit_data = [{"ProviderIdentification":{
        #     "ProviderID": "669465499",
        #     "ProviderQualifier": "MedicaidID"
        # },
        #          "VisitOtherID": "123456790",
        #          "SequenceID": 20220510105655,
        #          "EmployeeQualifier": "EmployeeCustomID",
        #          "EmployeeIdentifier": "000099999",
        #          "ClientIDQualifier": "ClientCustomID",
        #         "ClientIdentifier" : "9999999999",
        #          "ClientID": "9999999999",
        #          "VisitCancelledIndicator": True,
        #          "PayerID": "PAAHPH",
        #          "PayerProgram": "PHC",
        #          "ProcedureCode": "T1019",
        #          "VisitTimeZone": "US/Eastern",
        #          "Modifier1" : "",
        #         "BillVisit" : True,
        #          "Calls": [
        #              {
        #                  "CallExternalID": "123456791",
        #                  "CallDateTime": "2022-08-28T16:02:26Z",
        #                  "CallAssignment": "Time In",
        #                  "CallType": "Other",
        #                  "ProcedureCode": "T1019",
        #                  "VisitLocationType": 1,
        #                  "ClientIdentifierOnCall": "9999999999",
        #
        #              }
        #          ],
        #          "Tasks": [
        #              {
        #                  "TaskID": 32,
        #                  "TaskReading": "98.6",
        #                  "TaskRefused": False
        #              }
        #          ]
        #          }]

        # sql_db.db_connect(self.env.cr.dbname).cursor()