from odoo import fields, models, api


class AutomateProgramType(models.Model):
    _name = 'ks_project_task.automate_program_type'

    def automate_program_type(self):
        query = """update project_project
        set program_type = 'support_brokering' 
        where program_type = 'support_broking'"""
        self.env.cr.execute(query)

        query = """update account_analytic_line
                set program_type = 'support_brokering' 
                where program_type = 'support_broking'"""
        self.env.cr.execute(query)

        query = """update crm_lead
                set program_type = 'support_brokering' 
                where program_type = 'support_broking'"""
        self.env.cr.execute(query)

        query = """update res_partner
                set program_type = 'support_brokering' 
                where program_type = 'support_broking'"""
        self.env.cr.execute(query)

        query = """update project_project
                set program_type = 'htts' 
                where program_type = 'httss'"""
        self.env.cr.execute(query)

        query = """update account_analytic_line
                        set program_type = 'htts' 
                        where program_type = 'httss'"""
        self.env.cr.execute(query)

        query = """update crm_lead
                        set program_type = 'htts' 
                        where program_type = 'httss'"""
        self.env.cr.execute(query)

        query = """update res_partner
                        set program_type = 'htts' 
                        where program_type = 'httss'"""
        self.env.cr.execute(query)

        # transfer data of employee_ssn_temp to employee_ssn_temp_base
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            if employee.employee_ssn_temp and not employee.employee_ssn_temp_base:
                employee.employee_ssn_temp_base = employee.employee_ssn_temp


