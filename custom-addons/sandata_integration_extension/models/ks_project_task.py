import pytz
import werkzeug

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)
DEFAULT_SERVER_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class ProjectTaskInherit(models.Model):
    _inherit = "project.task"

    so_line_wizard = fields.Many2one('sale.order.line', string="Sale order Item Wizard")
    child_line_location_wiz = fields.Many2one('res.partner', string="Location")
    comment = fields.Text(string="Comment")
    ks_user_is_checked_out = fields.Boolean('Is Checked Out')

    def open_service_note_line(self, form_view_id=None, kwargs=None, ids=None):
        # survey_id = self.project_id.ks_survey
        # url = werkzeug.urls.url_join(survey_id.get_base_url(), survey_id.get_start_url()) if survey_id else False
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url,
        #     'target': 'new',
        # }
        return self.env['project.task'].with_context(from_note=True, survey_id=self.project_id.ks_survey,
                                                     task_ids=self.project_id.task_ids.ids).timesheet_sign_out(kwargs)



    def timesheet_sign_in(self, task_id, lat, lng, **kwargs):
        """
        Method to handle latitude and longitude data.
        - task_id: The ID of the task (resId from JavaScript).
        - lat: Latitude value.
        - lng: Longitude value.
        - kwargs: Additional keyword arguments (e.g., mode, context).
        """
        _logger.info("+++++++++++++++++++++++++ Check In +++++++++++++++++++++++++++++++++")
        _logger.info(f"Task ID: {task_id}, Latitude: {lat}, Longitude: {lng}")
        _logger.info(f"kwargs: {kwargs}")

        # Ensure the task exists
        task = self.env['project.task'].browse(task_id)
        if not task:
            raise UserError(_("Task not found."))

        # Check if the task has a project or if the context has 'from_delay_reason'
        if not (task.project_id or self.env.context.get('from_delay_reason')):
            return self._show_attendance_confirmation_wizard(kwargs)

        # Initialize required objects
        project_task_obj = self.env['project.task']
        via_atten_line_obj = self.env['via.attendance.line']
        user = self.env.user
        company = self.env.company

        # Find the employee for the current user
        employee_id = self.env['hr.employee'].search([
            ('user_id', '=', user.id),
            ('company_id', '=', company.id)
        ], limit=1)

        if not employee_id:
            raise ValidationError(_("Please create an employee for the current user."))

        # Determine the task IDs to process
        task_ids = task if task.project_id.program_type not in ['ihcs', 'ihcs_2_1', 'ihcs_e', 'companion', 'cps', 'cpse'] else self.env['project.task'].browse(self.env.context.get('tasks', task.id))

        # Handle check-in time and latitude/longitude
        if self.env.context.get('create_attendance'):
            lat_long = self.get_partner_lat_long(self.env.context.get('partner_id'))
            kwargs = kwargs or {}
            kwargs.update(lat_long)
            kwargs.update({'check_in_time': self.env.context.get('check_in_time')})

        # Process each task
        for record in task_ids:
            float_diff = 0.0
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            current_time = datetime.now(local).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            c_time = datetime.strptime(current_time, DEFAULT_SERVER_DATETIME_FORMAT)

            # Check planned date and calculate delay
            if record.planned_date_begin:
                start_date = pytz.utc.localize(record.planned_date_begin).astimezone(local).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)

                delay_time = self.env['ir.config_parameter'].sudo().get_param('delay_time', default=False)
                if delay_time:
                    time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(delay_time) * 60, 60))
                    start_date += timedelta(days=(c_time - start_date).days, hours=int(time.split(':')[0]), minutes=int(time.split(':')[1]))

                    if c_time > start_date:
                        diff = c_time - start_date
                        vals = str(diff).split(':')
                        t, hours = divmod(float(vals[0]), 24)
                        t, minutes = divmod(float(vals[1]), 60)
                        minutes = minutes / 60.0
                        float_diff = hours + minutes

                if float_diff:
                    kwargs = kwargs or {}
                    kwargs.update({'delay_time': float_diff})
                    return self._show_delay_reason_wizard(kwargs, record.id)
            else:
                raise ValidationError(_("Please select a planned date."))

            # Create attendance line
            via_line_ids = via_atten_line_obj.search([
                ('employee_id', '=', employee_id.id),
                ('check_out_time', '=', False),
                ('company_id', '=', company.id),
                ('task_id', '!=', False)
            ], limit=1)

            if via_line_ids:
                raise ValidationError(_("You can only check in to one task at a time. Please check out from task %s.", via_line_ids.task_id.name))

            check_in_time = kwargs.get('check_in_time', fields.Datetime.now())
            is_manual = bool(kwargs.get('check_in_time'))

            via_atten_line_id = via_atten_line_obj.create({
                'date': fields.Date.today(),
                'task_id': record.id,
                'check_in_time': check_in_time,
                'check_in_latitude': lat,
                'check_in_longitude': lng,
                'delay_time_differance': kwargs.get('delay_time', 0.0),
                'temperature': kwargs.get('temperature'),
                'delay_reason': kwargs.get('delay_reason'),
                'is_manual': is_manual,
            })

            # Handle Sandata integration
            if record.project_id.program_type in ['ihcs', 'ihcs_2_1', 'ihcs_e', 'companion', 'cps', 'cpse']:
                sandata_config_id = self.env['sandata.configuration'].sudo().search([
                    ('state', '=', 'done'),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not sandata_config_id:
                    raise ValidationError(_("Please configure Sandata settings."))

                headers = project_task_obj.prepare_sandata_headers(sandata_config_id)
                provider = project_task_obj.prepare_sandata_provider(sandata_config_id)

                if sandata_config_id.mode == 'enabled':
                    project_task_obj.create_edit_sandata_record(record, via_atten_line_id,
                                                               sandata_config_id.prod_client_url,
                                                               sandata_config_id.prod_employee_url,
                                                               sandata_config_id.prod_visit_url,
                                                               'check_in', headers, provider,
                                                               sandata_config_id.prod_get_client_url,
                                                               sandata_config_id.prod_get_employee_url,
                                                               sandata_config_id.prod_get_visit_url,
                                                               sandata_config_id.mode)
                elif sandata_config_id.mode == 'test':
                    project_task_obj.create_edit_sandata_record(record, via_atten_line_id,
                                                               sandata_config_id.test_client_url,
                                                               sandata_config_id.test_employee_url,
                                                               sandata_config_id.test_visit_url,
                                                               'check_in', headers, provider,
                                                               sandata_config_id.test_get_client_url,
                                                               sandata_config_id.test_get_employee_url,
                                                               sandata_config_id.test_get_visit_url,
                                                               sandata_config_id.mode)

        return True

    def _show_attendance_confirmation_wizard(self, kwargs):
        """
        Show the attendance confirmation wizard.
        """
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
            'context': {
                'default_msg_description': message_id.confirm_message,
                'message_id': message_id.id,
                'kwargs': kwargs,
                'tasks': self.ids
            }
        }

    def _show_delay_reason_wizard(self, kwargs, task_id):
        """
        Show the delay reason wizard.
        """
        form_view_id = self.env.ref('sandata_integration.delay_reason_wizard_form_view').id
        return {
            'name': _('Delay Reason'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'delay.reason.wizard',
            'view_id': form_view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'kwargs': kwargs,
                'tasks': task_id
            }
        }
        # active_id = self.env.context.get('active_id')  # Use .get() to avoid KeyError

        # if not active_id:
        #     raise UserError(_("No active task found."))  # Handle missing active_id

        # task = self.env['project.task'].browse(active_id)

        # return {
        #     'context': {
        #         'default_partner_id': task.partner_id.id if task.partner_id else False,
        #         'default_sale_line_id': task.sale_line_id.id if task.sale_line_id else False,
        #         'default_task_id': task.id,
        #     },
        #     'name': _('Other Location'),
        #     'view_mode': 'form',
        #     'res_model': 'other.location.wizard',
        #     'type': 'ir.actions.act_window',
        #     'target': 'new',
        # }


    # def set_other_location(self, kwargs=None):
    #     try:
    #         # if self.env.context.get('from_note') or self.env.context.get('create_attendance') or \
    #         #         self.env.context.get('from_delay_reason') or (self.project_id and not self.project_id.program_type or \
    #         #                                                   self.project_id.program_type not in ['ihcs', 'ihcs_e',
    #         #                                                                                        'ihcs_2_1',
    #         #                                                                                        'ihcs_e',
    #         #                                                                                        'companion']):
    #
    #         if self.project_id or self.env.context.get('from_other_location'):
    #             project_task_obj = self.env['project.task']
    #             via_atten_line_obj = self.env['via.attendance.line']
    #
    #             task_ids = False
    #             if self.project_id and self.project_id.program_type not in ['ihcs', 'ihcs_e', 'ihcs_2_1', 'ihcs_e',
    #                                                                         'companion']:
    #                 task_ids = self
    #             else:
    #                 task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
    #                 if not task_ids:
    #                     task_ids = self
    #
    #             if employee_id:
    #                 for record in task_ids:
    #                     # via_line_ids = via_atten_line_obj.search([
    #                     #     ('employee_id', '=', employee_id.id),
    #                     #     ('check_out_time', '=', False),
    #                     #     ('company_id', '=', company.id),
    #                     #     ('task_id', '!=', False)], limit=1)
    #                     # if via_line_ids:
    #                     #     raise ValidationError(
    #                     #         _("""At a time you can Check-in in the one task only. Please checkout from %s task is %s.""",
    #                     #           via_line_ids.task_id.project_id.name, via_line_ids.task_id.name))
    #
    #                     check_in_time = False
    #                     is_manual = False
    #                     if kwargs.get('check_in_time'):
    #                         check_in_time = kwargs.get('check_in_time')
    #                         is_manual = True
    #                     else:
    #                         check_in_time = fields.Datetime.now()
    #
    #                     via_atten_line_id = via_atten_line_obj.create({
    #                         'so_line': kwargs.get('so_line')
    #                     })
    #
    #                     if record.project_id and record.project_id.program_type and record.project_id.program_type in [
    #                         'ihcs', 'ihcs_e',
    #                         'ihcs_2_1', 'ihcs_e',
    #                         'companion']:
    #                         sandata_config_id = self.env['sandata.configuration'].sudo().search([('state', '=', 'done'),
    #                                                                                              ('company_id', '=',
    #                                                                                               self.env.company.id)],
    #                                                                                             limit=1)
    #                         if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
    #                             headers = project_task_obj.prepare_sandata_headers(sandata_config_id)
    #                             provider = project_task_obj.prepare_sandata_provider(sandata_config_id)
    #                             if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
    #                                 project_task_obj.create_edit_sandata_record(record, via_atten_line_id,
    #                                                                             sandata_config_id.prod_client_url,
    #                                                                             sandata_config_id.prod_employee_url,
    #                                                                             sandata_config_id.prod_visit_url,
    #                                                                             'check_in', headers, provider,
    #                                                                             sandata_config_id.prod_get_client_url,
    #                                                                             sandata_config_id.prod_get_employee_url,
    #                                                                             sandata_config_id.prod_get_visit_url,
    #                                                                             sandata_config_id.mode)
    #                             if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
    #                                 project_task_obj.create_edit_sandata_record(record, via_atten_line_id,
    #                                                                             sandata_config_id.test_client_url,
    #                                                                             sandata_config_id.test_employee_url,
    #                                                                             sandata_config_id.test_visit_url,
    #                                                                             'check_in', headers, provider,
    #                                                                             sandata_config_id.test_get_client_url,
    #                                                                             sandata_config_id.test_get_employee_url,
    #                                                                             sandata_config_id.test_get_visit_url,
    #                                                                             sandata_config_id.mode)
    #                         else:
    #                             raise ValidationError(_("""Please set Sandata Configuration"""))
    #             else:
    #                 raise ValidationError(_("Please Create Employee For Current User"))
    #
    #     except (OSError, Exception) as err:
    #         raise ValidationError(_("%s", tools.ustr(err)))
    #     return True

    # def timesheet_sign_out(self, kwargs=None):
    #     """
    #     :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
    #     """
    #     try:
    #         # if self.env.context.get('from_note'):
    #         if self:
    #             if self.project_id and self.project_id.program_type not in ['ihcs', 'ihcs_e', 'ihcs_2_1', 'ihcs_e',
    #                                                                         'companion']:
    #                 task_ids = self
    #             else:
    #                 if self.env.context.get('tasks'):
    #                     task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
    #                 else:
    #                     # task_ids = self.env['project.task'].browse(self.env.context.get('params').get('id'))
    #                     task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
    #             via_atten_line_obj = self.env['via.attendance.line']
    #             analytic_line_obj = self.env['account.analytic.line']
    #             via_service_note_obj = self.env['via.service.note']
    #             user = self.env.user
    #             company = self.env.company
    #             employee_id = self.env['hr.employee'].search([
    #                 ('user_id', '=', user.id),
    #                 ('company_id', '=', company.id)], limit=1)
    #             if employee_id and task_ids:
    #                 worked_hours = 0.0
    #                 for record in task_ids:
    #                     user_tz = self.env.user.tz or pytz.utc
    #                     local = pytz.timezone(user_tz)
    #                     current_time = datetime.now(local).strftime('%Y-%m-%d %H:%M:%S')
    #                     c_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
    #                     # if (record.planned_date_begin.date() < c_time.date()) and (
    #                     #         record.planned_date_end.date() >= c_time.date()):
    #                     via_line_ids = via_atten_line_obj.search([
    #                         ('employee_id', '=', employee_id.id),
    #                         ('check_out_time', '=', False),
    #                         ('task_id', '!=', record.id),
    #                         ('task_id', '!=', False),
    #                         ('company_id', '=', company.id)], limit=1)
    #                     if via_line_ids:
    #                         raise ValidationError(
    #                             _("""Please Check-out from %s task first.""", via_line_ids.task_id.name))
    #                     sign_in_line = via_atten_line_obj.search([
    #                         ('employee_id', '=', employee_id.id),
    #                         ('company_id', '=', company.id),
    #                         ('task_id', '=', record.id),
    #                         ('check_out_time', '=', False)],
    #                         limit=1, order='id desc')
    #                     #       self.env.context.get('check_out_time'))
    #                     if sign_in_line:
    #                         # if not kwargs.get('isp_data'):
    #                         #     raise ValidationError(_("""Please Enter Service Note Line."""))
    #                         if sign_in_line.is_manual:
    #                             if self.env.context.get('from_checkout'):
    #                                 if kwargs is None:
    #                                     kwargs = {}
    #                                     form_view_id = self.env.ref(
    #                                         'sandata_integration.via_service_note_wizard_form_view').id
    #                                     if self.env.context.get('from_checkout'):
    #                                         kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
    #                                         task_id = self.env['project.task'].sudo().browse(self.ids)
    #                                         if record:
    #                                             if record[0].sale_line_id and record[
    #                                                 0].sale_line_id.order_id.partner_id and \
    #                                                     record[0].sale_line_id.order_id.partner_id.isp_ids:
    #                                                 isp_ids = record[
    #                                                     0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                                                     lambda isp: isp.product_id.id == record[
    #                                                         0].sale_line_id.product_id.id).sorted(key=lambda r: r.id)
    #                                                 if isp_ids:
    #                                                     list_data = []
    #                                                     if isp_ids[-1].outcome_phrase:
    #                                                         list_data.append(
    #                                                             (0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                                     'isp_id': isp_ids[-1].id
    #                                                                     }))
    #                                                     # if isp_ids[-1].reason_for_outcome:
    #                                                     #     list_data.append((0, 0, {
    #                                                     #         'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                                                     #         'isp_id': isp_ids[-1].id
    #                                                     #         }))
    #                                                     # if isp_ids[-1].outcome_statement:
    #                                                     #     list_data.append(
    #                                                     #         (0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                                                     #                 'isp_id': isp_ids[-1].id
    #                                                     #                 }))
    #                                                     # if isp_ids[-1].actions_taken:
    #                                                     #     list_data.append(
    #                                                     #         (0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                                                     #                 'isp_id': isp_ids[-1].id
    #                                                     #                 }))
    #                                                     # if isp_ids[-1].progress_status:
    #                                                     #     list_data.append(
    #                                                     #         (0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                                                     #                 'isp_id': isp_ids[-1].id
    #                                                     #                 }))
    #                                                     # return {
    #                                                     #     'name': _('Service Notes'),
    #                                                     #     'view_type': 'form',
    #                                                     #     'view_mode': 'form',
    #                                                     #     'res_model': 'via.service.note.wizard',
    #                                                     #     'view_id': form_view_id,
    #                                                     #     'type': 'ir.actions.act_window',
    #                                                     #     'target': 'new',
    #                                                     #     'context': {'kwargs': kwargs,
    #                                                     #                 'tasks': self.env.context.get('tasks'),
    #                                                     #                 'default_service_note_survey_ids': list_data}
    #                                                     # }
    #                                                     return self.open_service_note_line()
    #                                                 else:
    #                                                     return self.open_service_note_line(form_view_id, kwargs,
    #                                                                                        self.env.context.get(
    #                                                                                            'tasks'))
    #                                             else:
    #                                                 return self.open_service_note_line(form_view_id, kwargs,
    #                                                                                    self.env.context.get('tasks'))
    #                                 sign_in_line.sudo().write({
    #                                     'check_out_time': kwargs.get('check_out_time'),
    #                                     'check_out_latitude': sign_in_line.check_in_latitude,
    #                                     'check_out_longitude': sign_in_line.check_in_longitude,
    #                                     # 'note': kwargs.get('note') or '',
    #                                     'is_checkout_done': True
    #                                 })
    #                             else:
    #                                 raise ValidationError(_("""Please do checkout from the manually"""))
    #                         if not sign_in_line.is_manual and not self.env.context.get('from_checkout'):
    #                             sign_in_line.sudo().write({'check_out_time': fields.Datetime.now(),
    #                                                        'check_out_latitude': kwargs.get('lat'),
    #                                                        'check_out_longitude': kwargs.get('lng'),
    #                                                        'note': kwargs.get('note') or ''
    #                                                        })
    #                         hours_spent = 0.0
    #                         if record.project_id and record.project_id.program_type and record.project_id.program_type not in [
    #                             'support_brokering',
    #                             'htts']:
    #                             duration = (
    #                                                    sign_in_line.check_out_time - sign_in_line.check_in_time).total_seconds() / 3600
    #                             hours_spent = round(duration, 2)
    #                         analytic_line_id = analytic_line_obj.sudo().create({'date': sign_in_line.date,
    #                                                                             'employee_id': employee_id.id,
    #                                                                             'name': sign_in_line.description or '',
    #                                                                             'check_in_time': sign_in_line.check_in_time,
    #                                                                             'check_out_time': sign_in_line.check_out_time,
    #                                                                             'latitude_in': sign_in_line.check_in_latitude,
    #                                                                             'longitude_in': sign_in_line.check_in_longitude,
    #                                                                             'latitude_out': sign_in_line.check_out_latitude,
    #                                                                             'longitude_out': sign_in_line.check_out_longitude,
    #                                                                             'task_id': sign_in_line.task_id.id,
    #                                                                             'unit_amount': hours_spent,
    #                                                                             'program_type': record.project_id.program_type,
    #                                                                             # 'duration_unit_amount': hours_spent,
    #                                                                             # 'unit_amount_validate':  hours_spent,
    #                                                                             'is_so_line_edited': False,
    #                                                                             'product_uom_id': sign_in_line.task_id.sale_line_id.order_id.timesheet_encode_uom_id.id
    #                                                                             })
    #                         if kwargs.get('isp_data'):
    #                             for isp_data in kwargs.get('isp_data'):
    #                                 via_service_note_obj.sudo().create(
    #                                     {'project_id': sign_in_line.task_id.project_id.id,
    #                                      'task_id': sign_in_line.task_id.id,
    #                                      'via_attendance_line_id': sign_in_line.id,
    #                                      'partner_id': sign_in_line.task_id.partner_id.id or False,
    #                                      'outcome_phrase': isp_data.get('outcome_phrase') or '',
    #                                      'reason_for_outcome': isp_data.get('reason_for_outcome') or '',
    #                                      'outcome_statement': isp_data.get('outcome_statement') or '',
    #                                      'actions_taken': isp_data.get('actions_taken') or '',
    #                                      'progress_status': isp_data.get('progress_status') or '',
    #                                      'survey_answer': isp_data.get('survey_answer') or '',
    #                                      'start_time': isp_data.get('start_time') or 0,
    #                                      'end_time': isp_data.get('end_time') or 0,
    #                                      'service_delivery_date': isp_data.get('service_delivery_date') or False,
    #                                      'description_of_activities': isp_data.get('note') or '',
    #                                      'note': isp_data.get('note') or '',
    #                                      'isp_id': isp_data.get('isp_id'),
    #                                      'employee_id': self.env.user.employee_id.id,
    #                                      'user_id': self.env.user.id,
    #                                      'account_analytic_line_id': analytic_line_id.id})
    #                         if record.project_id and record.project_id.program_type and record.project_id.program_type in [
    #                             'ihcs', 'ihcs_e',
    #                             'ihcs_2_1', 'ihcs_e',
    #                             'companion']:
    #                             sandata_config_id = self.env['sandata.configuration'].sudo().search(
    #                                 [('state', '=', 'done'),
    #                                  ('company_id', '=', self.env.company.id)], limit=1)
    #                             if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
    #                                 headers = self.prepare_sandata_headers(sandata_config_id)
    #                                 provider = self.prepare_sandata_provider(sandata_config_id)
    #                                 if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
    #                                     self.create_edit_sandata_record(record, sign_in_line,
    #                                                                     sandata_config_id.prod_client_url,
    #                                                                     sandata_config_id.prod_employee_url,
    #                                                                     sandata_config_id.prod_visit_url,
    #                                                                     'check_out', headers, provider,
    #                                                                     sandata_config_id.prod_get_employee_url,
    #                                                                     sandata_config_id.prod_get_visit_url,
    #                                                                     sandata_config_id.mode)
    #                                 if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
    #                                     self.create_edit_sandata_record(record, sign_in_line,
    #                                                                     sandata_config_id.test_client_url,
    #                                                                     sandata_config_id.test_employee_url,
    #                                                                     sandata_config_id.test_visit_url,
    #                                                                     'check_out', headers, provider,
    #                                                                     sandata_config_id.test_get_client_url,
    #                                                                     sandata_config_id.test_get_employee_url,
    #                                                                     sandata_config_id.test_get_visit_url,
    #                                                                     sandata_config_id.mode)
    #                             else:
    #                                 raise ValidationError(_("""Please set Sandata Configuration"""))
    #                     else:
    #                         raise ValidationError(_("""Please Check-in first."""))
    #                     # else:
    #                     #     raise ValidationError(_("Check-out time must be between planned date"))
    #             else:
    #                 raise ValidationError(_("Please Create Employee For Current User"))
    #         else:
    #             form_view_id = self.env.ref('sandata_integration.via_service_note_wizard_form_view').id
    #             if self.env.context.get('from_checkout'):
    #                 if kwargs is None:
    #                     kwargs = {}
    #                 kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
    #                 task_id = self.env['project.task'].sudo().browse(self.ids)
    #                 if not task_id:
    #                     if self.project_id and self.project_id.program_type not in ['ihcs', 'ihcs_e', 'ihcs_2_1',
    #                                                                                 'ihcs_e',
    #                                                                                 'companion']:
    #                         task_id = self
    #                     else:
    #                         task_id = self.env['project.task'].browse(self.env.context.get('tasks'))
    #                 if task_id:
    #                     if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
    #                             task_id[0].sale_line_id.order_id.partner_id.isp_ids:
    #                         isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                             lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(
    #                             key=lambda r: r.id)
    #                         if isp_ids:
    #                             list_data = []
    #                             if isp_ids[-1].outcome_phrase:
    #                                 list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                          'isp_id': isp_ids[-1].id
    #                                                          }))
    #                             # if isp_ids[-1].reason_for_outcome:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].outcome_statement:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].actions_taken:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].progress_status:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             return {
    #                                 'name': _('Service Notes'),
    #                                 'view_type': 'form',
    #                                 'view_mode': 'form',
    #                                 'res_model': 'via.service.note.wizard',
    #                                 'view_id': form_view_id,
    #                                 'type': 'ir.actions.act_window',
    #                                 'target': 'new',
    #                                 'context': {'kwargs': kwargs,
    #                                             'tasks': self.env.context.get('tasks'),
    #                                             'default_service_note_survey_ids': list_data}
    #                             }
    #                         else:
    #                             return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
    #                     else:
    #                         return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
    #             else:
    #                 task_id = self.env['project.task'].sudo().browse(self.ids)
    #                 if task_id:
    #                     if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
    #                             task_id[0].sale_line_id.order_id.partner_id.isp_ids:
    #                         isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                             lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(
    #                             key=lambda r: r.id)
    #                         if isp_ids:
    #                             list_data = []
    #                             if isp_ids[-1].outcome_phrase:
    #                                 list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                          'isp_id': isp_ids[-1].id
    #                                                          }))
    #                             # if isp_ids[-1].reason_for_outcome:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].outcome_statement:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].actions_taken:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #                             # if isp_ids[-1].progress_status:
    #                             #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                             #                              'isp_id': isp_ids[-1].id
    #                             #                              }))
    #
    #                             return {
    #                                 'name': _('Service Notes'),
    #                                 'view_type': 'form',
    #                                 'view_mode': 'form',
    #                                 'res_model': 'via.service.note.wizard',
    #                                 'view_id': form_view_id,
    #                                 'type': 'ir.actions.act_window',
    #                                 'target': 'new',
    #                                 'context': {'kwargs': kwargs,
    #                                             'tasks': self.ids,
    #                                             'default_service_note_survey_ids': list_data}
    #                             }
    #                         else:
    #                             return self.open_service_note_line(form_view_id, kwargs, self.ids)
    #                     else:
    #                         return self.open_service_note_line(form_view_id, kwargs, self.ids)
    #     except (OSError, Exception) as err:
    #         # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
    #         # self.create_sandata_log(err, task_ids)
    #         raise ValidationError(_("%s", tools.ustr(err)))
    #     return self.open_service_note_line(kwargs, self.ids)
    
    

    def timesheet_sign_out(self, task_id, lat, lng, **kwargs):
        """
        Method to handle check-out for a task with latitude and longitude data.
        - task_id: The ID of the task (resId from JavaScript).
        - lat: Latitude value.
        - lng: Longitude value.
        - kwargs: Additional keyword arguments (e.g., mode, context).
        """
        _logger.info("+++++++++++++++++++++++++ Check Out +++++++++++++++++++++++++++++++++")
        _logger.info(f"Task ID: {task_id}, Latitude: {lat}, Longitude: {lng}")
        _logger.info(f"kwargs: {kwargs}")

        # Ensure the task exists
        task = self.env['project.task'].browse(task_id)
        if not task:
            raise UserError(_("Task not found."))

        # Initialize required objects
        via_atten_line_obj = self.env['via.attendance.line']
        analytic_line_obj = self.env['account.analytic.line']
        user = self.env.user
        company = self.env.company

        # Find the employee for the current user
        employee_id = self.env['hr.employee'].search([
            ('user_id', '=', user.id),
            ('company_id', '=', company.id)
        ], limit=1)

        if not employee_id:
            raise ValidationError(_("Please create an employee for the current user."))

        # Ensure kwargs is always a dictionary
        kwargs = kwargs or {}
        self = task
        # Process each task
        for record in self:
            # Check if the user is already checked out
            # if record.ks_user_is_checked_out:
            #     _logger.info(f"User is already checked out from task {record.name}.")
            #     continue
            _logger.info("++++++++++++++++++ %s", record.ks_user_is_checked_out)
            # Find any open attendance lines for the employee
            via_line_ids = via_atten_line_obj.search([
                ('employee_id', '=', employee_id.id),
                ('check_out_time', '=', False),
                ('task_id', '!=', record.id),
                ('company_id', '=', company.id)
            ], limit=1)

            if via_line_ids:
                raise ValidationError(_("Please check out from task %s first.", via_line_ids.task_id.name))

            # Find the latest check-in line for the current task
            sign_in_line = via_atten_line_obj.search([
                ('employee_id', '=', employee_id.id),
                ('company_id', '=', company.id),
                ('task_id', '=', record.id),
                ('check_out_time', '=', False)
            ], limit=1, order='id desc')

            if sign_in_line:
                # Update the check-out time and location
                sign_in_line.write({
                    'check_out_time': fields.Datetime.now(),
                    'check_out_latitude': lat,
                    'check_out_longitude': lng,
                })

                # Calculate hours spent
                duration = (sign_in_line.check_out_time - sign_in_line.check_in_time).total_seconds() / 3600
                hours_spent = round(duration, 2)

                # Create an analytic line for the time spent
                analytic_line_obj.create({
                    'date': sign_in_line.date,
                    'employee_id': employee_id.id,
                    'name': sign_in_line.description or '',
                    'check_in_time': sign_in_line.check_in_time,
                    'check_out_time': sign_in_line.check_out_time,
                    'latitude_in': sign_in_line.check_in_latitude,
                    'longitude_in': sign_in_line.check_in_longitude,
                    'latitude_out': sign_in_line.check_out_latitude,
                    'longitude_out': sign_in_line.check_out_longitude,
                    'task_id': sign_in_line.task_id.id,
                    'unit_amount': hours_spent
                })

                # Mark the task as checked out
                record.ks_user_is_checked_out = True
                _logger.info(f"User checked out from task {record.name}.")

            else:
                raise ValidationError(_("Please check in first."))

        # Refresh the stored values
        # self.env['project.task'].search([('id', 'in', self.ids)]).refresh()
        _logger.info("Stored values refreshed.")

        return True
    # def timesheet_sign_out(self, kwargs=None):
    #     """
    #     :param kwargs: {'lat': FLOAT, 'lng': FLOAT, 'mode': 'readonly | edit'}
    #     """
    #     _logger.info("+++++++++++++++++++++++++ check out+++++++++++++++++++++++++++++++++")
    #     _logger.info(kwargs)
    #     # try:
    #     if self.env.context.get('from_note'):
    #         if self.project_id and self.project_id.program_type not in ['ihcs', 
    #                                                                     # 'ihcs_e',
    #                                                                     'ihcs_2_1', 'ihcs_e',
    #                                                                     'companion', 'cps', 'cpse']:
    #             task_ids = self
    #         else:
    #             if self.env.context.get('tasks'):
    #                 task_ids = self.env['project.task'].browse(self.env.context.get('tasks'))
    #             else:
    #                 # task_ids = self.env['project.task'].browse(self.env.context.get('params').get('id'))
    #                 task_ids = self.env['project.task'].browse(self.env.context.get('task_ids'))
    #         via_atten_line_obj = self.env['via.attendance.line']
    #         analytic_line_obj = self.env['account.analytic.line']
    #         via_service_note_obj = self.env['via.service.note']
    #         user = self.env.user
    #         company = self.env.company
    #         employee_id = self.env['hr.employee'].search([
    #             ('user_id', '=', user.id),
    #             ('company_id', '=', company.id)], limit=1)
    #         if employee_id and task_ids:
    #             worked_hours = 0.0
    #             for record in task_ids:
    #                 user_tz = self.env.user.tz or pytz.utc
    #                 local = pytz.timezone(user_tz)
    #                 current_time = datetime.now(local).strftime('%Y-%m-%d %H:%M:%S')
    #                 c_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
    #                 # if (record.planned_date_begin.date() < c_time.date()) and (
    #                 #         record.planned_date_end.date() >= c_time.date()):
    #                 via_line_ids = via_atten_line_obj.search([
    #                     ('employee_id', '=', employee_id.id),
    #                     ('check_out_time', '=', False),
    #                     ('task_id', '!=', record.id),
    #                     ('task_id', '!=', False),
    #                     ('company_id', '=', company.id)], limit=1)
    #                 _logger.info("via_line_ids %s",via_line_ids)
    #                 _logger.info("via_line_ids %s",via_line_ids.check_out_time)
    #                 # if via_line_ids:
    #                 #     raise ValidationError(
    #                 #         _("""Please Check-out from %s task first.""", via_line_ids.task_id.name))
    #                 sign_in_line = via_atten_line_obj.search([
    #                     ('employee_id', '=', employee_id.id),
    #                     ('company_id', '=', company.id),
    #                     ('task_id', '=', record.id),
    #                     ('check_out_time', '=', False)],
    #                     limit=1, order='id desc')
    #                 #       self.env.context.get('check_out_time'))
                    
    #                 _logger.info('aaaaaaaa')
    #                 if sign_in_line:
    #                     # if not kwargs.get('isp_data'):
    #                     #     raise ValidationError(_("""Please Enter Service Note Line."""))
    #                     if sign_in_line.is_manual:
    #                         if self.env.context.get('from_checkout'):
    #                             if kwargs is None:
    #                                 kwargs = {}
    #                                 form_view_id = self.env.ref(
    #                                     'sandata_integration.via_service_note_wizard_form_view').id
    #                                 if self.env.context.get('from_checkout'):
    #                                     kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
    #                                     task_id = self.env['project.task'].sudo().browse(self.ids)
    #                                     if record:
    #                                         if record[0].sale_line_id and record[
    #                                             0].sale_line_id.order_id.partner_id and \
    #                                                 record[0].sale_line_id.order_id.partner_id.isp_ids:
    #                                             isp_ids = record[
    #                                                 0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                                                 lambda isp: isp.product_id.id == record[
    #                                                     0].sale_line_id.product_id.id).sorted(key=lambda r: r.id)
    #                                             if isp_ids:
    #                                                 list_data = []
    #                                                 if isp_ids[-1].outcome_phrase:
    #                                                     list_data.append(
    #                                                         (0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                                 'isp_id': isp_ids[-1].id
    #                                                                 }))
    #                                                 # if isp_ids[-1].reason_for_outcome:
    #                                                 #     list_data.append((0, 0, {
    #                                                 #         'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                                                 #         'isp_id': isp_ids[-1].id
    #                                                 #         }))
    #                                                 # if isp_ids[-1].outcome_statement:
    #                                                 #     list_data.append(
    #                                                 #         (0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                                                 #                 'isp_id': isp_ids[-1].id
    #                                                 #                 }))
    #                                                 # if isp_ids[-1].actions_taken:
    #                                                 #     list_data.append(
    #                                                 #         (0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                                                 #                 'isp_id': isp_ids[-1].id
    #                                                 #                 }))
    #                                                 # if isp_ids[-1].progress_status:
    #                                                 #     list_data.append(
    #                                                 #         (0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                                                 #                 'isp_id': isp_ids[-1].id
    #                                                 #                 }))
    #                                                 return {
    #                                                     'name': _('Service Notes'),
    #                                                     'view_type': 'form',
    #                                                     'view_mode': 'form',
    #                                                     'res_model': 'via.service.note.wizard',
    #                                                     'view_id': form_view_id,
    #                                                     'type': 'ir.actions.act_window',
    #                                                     'target': 'new',
    #                                                     'context': {'kwargs': kwargs,
    #                                                                 'tasks': self.env.context.get('tasks'),
    #                                                                 'default_service_note_survey_ids': list_data}
    #                                                 }
    #                                             else:
    #                                                 return self.open_service_note_line(form_view_id, kwargs,
    #                                                                                     self.env.context.get(
    #                                                                                         'tasks'))
    #                                         else:
    #                                             return self.open_service_note_line(form_view_id, kwargs,
    #                                                                                 self.env.context.get('tasks'))
    #                             sign_in_line.sudo().write({
    #                                 'check_out_time': kwargs.get('check_out_time'),
    #                                 'check_out_latitude': sign_in_line.check_in_latitude,
    #                                 'check_out_longitude': sign_in_line.check_in_longitude,
    #                                 # 'note': kwargs.get('note') or '',
    #                                 'is_checkout_done': True
    #                             })
    #                         else:
    #                             raise ValidationError(_("""Please do checkout from the manually"""))
    #                     if not sign_in_line.is_manual and not self.env.context.get('from_checkout'):
    #                         kwargs = kwargs or {}  # Ensure kwargs is always a dictionary

    #                         sign_in_line.sudo().write({
    #                             'check_out_time': fields.Datetime.now(),
    #                             'check_out_latitude': kwargs.get('lat', False),  # Use .get() with default value
    #                             'check_out_longitude': kwargs.get('lng', False),
    #                             'note': kwargs.get('note', '')
    #                         })

    #                     hours_spent = 0.0
    #                     if record.project_id and record.project_id.program_type and record.project_id.program_type not in [
    #                         'support_brokering',
    #                         'htts']:
    #                         duration = (
    #                                                 sign_in_line.check_out_time - sign_in_line.check_in_time).total_seconds() / 3600
    #                         hours_spent = round(duration, 2)
    #                     analytic_line_id = analytic_line_obj.sudo().create({'date': sign_in_line.date,
    #                                                                         'employee_id': employee_id.id,
    #                                                                         'name': sign_in_line.description or '',
    #                                                                         'check_in_time': sign_in_line.check_in_time,
    #                                                                         'check_out_time': sign_in_line.check_out_time,
    #                                                                         'latitude_in': sign_in_line.check_in_latitude,
    #                                                                         'longitude_in': sign_in_line.check_in_longitude,
    #                                                                         'latitude_out': sign_in_line.check_out_latitude,
    #                                                                         'longitude_out': sign_in_line.check_out_longitude,
    #                                                                         'task_id': sign_in_line.task_id.id,
    #                                                                         'child_line_location': sign_in_line.task_id.child_line_location_wiz.id if sign_in_line.task_id.child_line_location_wiz.id else None,
    #                                                                         'comment':sign_in_line.task_id.comment,
    #                                                                         'unit_amount': hours_spent,
    #                                                                         'program_type': record.project_id.program_type,
    #                                                                         # 'duration_unit_amount': hours_spent,
    #                                                                         # 'unit_amount_validate':  hours_spent,
    #                                                                         'is_so_line_edited': False,
    #                                                                         'product_uom_id': sign_in_line.task_id.sale_line_id.order_id.timesheet_encode_uom_id.id
    #                                                                         })
    #                     if kwargs.get('isp_data'):
    #                         for isp_data in kwargs.get('isp_data'):
    #                             via_service_note_obj.sudo().create(
    #                                 {'project_id': sign_in_line.task_id.project_id.id,
    #                                     'task_id': sign_in_line.task_id.id,
    #                                     'via_attendance_line_id': sign_in_line.id,
    #                                     'partner_id': sign_in_line.task_id.partner_id.id or False,
    #                                     'outcome_phrase': isp_data.get('outcome_phrase') or '',
    #                                     'reason_for_outcome': isp_data.get('reason_for_outcome') or '',
    #                                     'outcome_statement': isp_data.get('outcome_statement') or '',
    #                                     'actions_taken': isp_data.get('actions_taken') or '',
    #                                     'progress_status': isp_data.get('progress_status') or '',
    #                                     'survey_answer': isp_data.get('survey_answer') or '',
    #                                     'start_time': isp_data.get('start_time') or 0,
    #                                     'end_time': isp_data.get('end_time') or 0,
    #                                     'service_delivery_date': isp_data.get('service_delivery_date') or False,
    #                                     'description_of_activities': isp_data.get('note') or '',
    #                                     'note': isp_data.get('note') or '',
    #                                     'isp_id': isp_data.get('isp_id'),
    #                                     'employee_id': self.env.user.employee_id.id,
    #                                     'user_id': self.env.user.id,
    #                                     'account_analytic_line_id': analytic_line_id.id})
    #                     if record.project_id and record.project_id.program_type and record.project_id.program_type in [
    #                         'ihcs', 
    #                         # 'ihcs_e',
    #                         'ihcs_2_1', 'ihcs_e',
    #                         'companion', 'cps', 'cpse']:
    #                         sandata_config_id = self.env['sandata.configuration'].sudo().search(
    #                             [('state', '=', 'done'),
    #                                 ('company_id', '=', self.env.company.id)], limit=1)
    #                         if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
    #                             headers = self.prepare_sandata_headers(sandata_config_id)
    #                             provider = self.prepare_sandata_provider(sandata_config_id)
    #                             if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
    #                                 self.create_edit_sandata_record(record, sign_in_line,
    #                                                                 sandata_config_id.prod_client_url,
    #                                                                 sandata_config_id.prod_employee_url,
    #                                                                 sandata_config_id.prod_visit_url,
    #                                                                 'check_out', headers, provider,
    #                                                                 sandata_config_id.prod_get_employee_url,
    #                                                                 sandata_config_id.prod_get_visit_url,
    #                                                                 sandata_config_id.mode)
    #                             if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
    #                                 self.create_edit_sandata_record(record, sign_in_line,
    #                                                                 sandata_config_id.test_client_url,
    #                                                                 sandata_config_id.test_employee_url,
    #                                                                 sandata_config_id.test_visit_url,
    #                                                                 'check_out', headers, provider,
    #                                                                 sandata_config_id.test_get_client_url,
    #                                                                 sandata_config_id.test_get_employee_url,
    #                                                                 sandata_config_id.test_get_visit_url,
    #                                                                 sandata_config_id.mode)
    #                         else:
    #                             raise ValidationError(_("""Please set Sandata Configuration"""))
    #                 else:
    #                     _logger.info('slslslsl')
    #                     raise ValidationError(_("""Please Check-in first."""))
    #                 # else:
    #                     # raise ValidationError(_("Check-out time must be between planned date"))
    #         else:
    #             raise ValidationError(_("Please Create Employee For Current User"))
    #     else:
    #         form_view_id = self.env.ref('sandata_integration.via_service_note_wizard_form_view').id
    #         if self.env.context.get('from_checkout'):
    #             if kwargs is None:
    #                 kwargs = {}
    #             kwargs.update({'check_out_time': self.env.context.get('check_out_time')})
    #             task_id = self.env['project.task'].sudo().browse(self.ids)
    #             if not task_id:
    #                 if self.project_id and self.project_id.program_type not in ['ihcs', 
    #                                                                             # 'ihcs_e', 
    #                                                                             'ihcs_2_1',
    #                                                                             'ihcs_e',
    #                                                                             'companion', 'cps', 'cpse']:
    #                     task_id = self
    #                 else:
    #                     task_id = self.env['project.task'].browse(self.env.context.get('tasks'))
    #             if task_id:
    #                 if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
    #                         task_id[0].sale_line_id.order_id.partner_id.isp_ids:
    #                     isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                         lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(
    #                         key=lambda r: r.id)
    #                     if isp_ids:
    #                         list_data = []
    #                         if isp_ids[-1].outcome_phrase:
    #                             list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                         'isp_id': isp_ids[-1].id
    #                                                         }))
    #                         # if isp_ids[-1].reason_for_outcome:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].outcome_statement:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].actions_taken:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].progress_status:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         return {
    #                             'name': _('Service Notes'),
    #                             'view_type': 'form',
    #                             'view_mode': 'form',
    #                             'res_model': 'via.service.note.wizard',
    #                             'view_id': form_view_id,
    #                             'type': 'ir.actions.act_window',
    #                             'target': 'new',
    #                             'context': {'kwargs': kwargs,
    #                                         'tasks': self.env.context.get('tasks'),
    #                                         'default_service_note_survey_ids': list_data}
    #                         }
    #                     else:
    #                         return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
    #                 else:
    #                     return self.open_service_note_line(form_view_id, kwargs, self.env.context.get('tasks'))
    #         else:
    #             task_id = self.env['project.task'].sudo().browse(self.ids)
    #             if task_id:
    #                 if task_id[0].sale_line_id and task_id[0].sale_line_id.order_id.partner_id and \
    #                         task_id[0].sale_line_id.order_id.partner_id.isp_ids:
    #                     isp_ids = task_id[0].sale_line_id.order_id.partner_id.isp_ids.filtered(
    #                         lambda isp: isp.product_id.id == task_id[0].sale_line_id.product_id.id).sorted(
    #                         key=lambda r: r.id)
    #                     if isp_ids:
    #                         list_data = []
    #                         if isp_ids[-1].outcome_phrase:
    #                             list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_phrase,
    #                                                         'isp_id': isp_ids[-1].id
    #                                                         }))
    #                         # if isp_ids[-1].reason_for_outcome:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].reason_for_outcome,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].outcome_statement:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].outcome_statement,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].actions_taken:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].actions_taken,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         # if isp_ids[-1].progress_status:
    #                         #     list_data.append((0, 0, {'outcome_phrase': isp_ids[-1].progress_status,
    #                         #                              'isp_id': isp_ids[-1].id
    #                         #                              }))
    #                         return {
    #                             'name': _('Service Notes'),
    #                             'view_type': 'form',
    #                             'view_mode': 'form',
    #                             'res_model': 'via.service.note.wizard',
    #                             'view_id': form_view_id,
    #                             'type': 'ir.actions.act_window',
    #                             'target': 'new',
    #                             'context': {'kwargs': kwargs,
    #                                         'tasks': self.ids,
    #                                         'default_service_note_survey_ids': list_data}
    #                         }
    #                     else:
    #                         return self.open_service_note_line(form_view_id, kwargs, self.ids)
    #                 else:
    #                     return self.open_service_note_line(form_view_id, kwargs, self.ids)
    #     # except (OSError, Exception) as err:
    #     #     # _logger.info("Failed to connect to %s server %s.", server.server_type, server.name, exc_info=True)
    #     #     # self.create_sandata_log(err, task_ids)
    #     #     raise ValidationError(_("%s", tools.ustr(err)))
    #     ks_task_ids = self.env['project.task'].browse(self.env.context.get('task_ids'))
    #     for task in ks_task_ids:
    #         task.ks_user_is_checked_out = False
    #     # survey_id = self.env.context.get('survey_id')
    #     # url = werkzeug.urls.url_join(survey_id.get_base_url(), survey_id.get_start_url()) if survey_id else False
    #     # return {
    #     #     'type': 'ir.actions.act_url',
    #     #     'url': url,
    #     #     'target': 'new',
    #     # }
    #     return True

    def open_survey_timesheet(self, kwargs=None):
        _logger.info('llls')
        self.ks_user_is_checked_out = False
        check_out_time = self.env['via.attendance.line'].browse(max(self.attendance_line_ids.ids)).check_out_time
        if check_out_time:
            _logger.info('llls')
            raise ValidationError(_("""Please Check-in first."""))
        else:
            url = werkzeug.urls.url_join(self.project_id.ks_survey.get_base_url(), self.project_id.ks_survey.get_start_url()) if self.project_id.ks_survey else False
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
