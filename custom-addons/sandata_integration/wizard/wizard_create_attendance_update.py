from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'wizard.create.attendance.update'

    task_id = fields.Many2one('project.task', 'task ID')
    update_visit = fields.Boolean('Update visit')
    exception_acknowledgement = fields.Boolean('Exception acknowledgement')
    exception_id = fields.Integer('Exception ID')
    reasoncode = fields.Char('Reason code')
    resolution_code = fields.Char('Resolution Code')
    adj_in_date = fields.Datetime('AdjInDateTime')
    adj_out_date = fields.Datetime('AdjOutDateTime')
    visit_id = fields.Char('Visit ID')
    reason_memo = fields.Char('Reason Memo')
    client_verified_times = fields.Boolean('Client Verified Times')
    client_signature = fields.Boolean('Client Signature')

    def action_create_attendance(self):
        project_task_obj = self.env['project.task']
        # attendance_id = max(self.task_id.attendance_line_ids.mapped('id'))
        via_atten_line_id = self.env['via.attendance.line'].browse(int(self.visit_id))
        if self.adj_in_date:
            via_atten_line_id.check_in_time = self.adj_in_date
        if self.adj_out_date:
            via_atten_line_id.check_out_time = self.adj_out_date
        sandata_config_id = self.env['sandata.configuration'].sudo().search([('state', '=', 'done'),
                                                                             ('company_id', '=',
                                                                              self.env.company.id)],
                                                                            limit=1)
        if sandata_config_id.authorize_account and sandata_config_id.authorize_provider and sandata_config_id.authorize_user_id and sandata_config_id.authorize_pass:
            headers = project_task_obj.prepare_sandata_headers(sandata_config_id)
            provider = project_task_obj.prepare_sandata_provider(sandata_config_id)
            if sandata_config_id.mode == 'enabled' and sandata_config_id.prod_employee_url and sandata_config_id.prod_client_url and sandata_config_id.prod_visit_url:
                project_task_obj.create_edit_sandata_record(self.task_id, via_atten_line_id,
                                                            sandata_config_id.prod_client_url,
                                                            sandata_config_id.prod_employee_url,
                                                            sandata_config_id.prod_visit_url,
                                                            'check_in', headers, provider,
                                                            sandata_config_id.prod_get_client_url,
                                                            sandata_config_id.prod_get_employee_url,
                                                            sandata_config_id.prod_get_visit_url,
                                                            sandata_config_id.mode, call_details=False,
                                                            attendance_update=self)
            if sandata_config_id.mode == 'test' and sandata_config_id.test_employee_url and sandata_config_id.test_client_url and sandata_config_id.test_visit_url:
                project_task_obj.create_edit_sandata_record(self.task_id, via_atten_line_id,
                                                            sandata_config_id.test_client_url,
                                                            sandata_config_id.test_employee_url,
                                                            sandata_config_id.test_visit_url,
                                                            'check_in', headers, provider,
                                                            sandata_config_id.test_get_client_url,
                                                            sandata_config_id.test_get_employee_url,
                                                            sandata_config_id.test_get_visit_url,
                                                            sandata_config_id.mode, call_details=False,
                                                            attendance_update=self)

