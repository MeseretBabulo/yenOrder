from odoo import api, fields, models, _


class AttendanceConfirmMessageWizard(models.TransientModel):
    _name = 'attendance.confirm.message.wizard'
    _description = 'Attendance Confirm Message Wizard'

    msg_description = fields.Html('Terms & Conditions')
    # is_agree = fields.Boolean("Agree?")
    via_atten_line_id = fields.Many2one('via.attendance.line')
    temperature = fields.Char('Temperature')

    def confirm_with_term_condition(self):
        pass

    def disagree_term_condition(self):
        task_id = self.env['project.task'].browse(self.env.context.get('active_id'))
        message_id = self.env['attendance.confirm.message'].browse(self.env.context.get('message_id'))
        if task_id and message_id:
            self.env['mail.message'].create({
                'subject': _('Disagree For Terms & Conditions'),
                'body': self.env.user.name + ' has disagreed with ' + message_id.name,
                'record_name': message_id.name,
                'email_from': task_id.project_id.user_id.partner_id.email,
                'reply_to': task_id.project_id.user_id.partner_id.email,
                'model': 'project.task',
                'res_id': task_id.id,
                'reply_to_force_new': True,
            })
