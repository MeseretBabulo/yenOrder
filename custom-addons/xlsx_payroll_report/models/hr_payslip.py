from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # salary_summary_ids = fields.One2many('salary.summary', 'payslip_run_id', string='Salary Summaries')
    summary_line_ids = fields.One2many('salary.summary.line', 'payslip_run_id', string='Summary Lines',
                                     compute='_compute_summary_lines', store=True, readonly=False)

    def action_compute_summary(self):
        for run in self:
            run.summary_line_ids.unlink()
            summary_lines = []
            
            # Initialize totals dictionary with both code and name as keys
            totals = {
                'NET': {'name': 'Net Salary', 'amount': 0.0},
                'GROSS': {'name': 'Gross', 'amount': 0.0},
                'BASIC': {'name': 'Basic Salary', 'amount': 0.0},
                'TA': {'name': 'Transport Allowance', 'amount': 0.0},
                'OT': {'name': 'Over Time', 'amount': 0.0},
                'PENS': {'name': 'Pension Tax Employ 11%', 'amount': 0.0},
                'LOAN': {'name': 'Staff Debtor-Loan', 'amount': 0.0},
                'PIT': {'name': 'Income Tax Payable', 'amount': 0.0},
                # Add other codes as needed
            }

            for slip in run.slip_ids:
                for line in slip.line_ids:
                    _logger.info("Processing line - Code: %s, Name: %s, Total: %s", 
                            line.code, line.name, line.total)
                    
                    if line.code in totals:
                        totals[line.code]['amount'] += line.total
                        _logger.info("Updated total for code %s: %s", 
                                line.code, totals[line.code]['amount'])

            # Create summary lines
            sequence = 1
            for code, data in totals.items():
                if data['amount'] != 0 or code in ['NET', 'GROSS', 'BASIC']:  # Always include these even if zero
                    summary_lines.append((0, 0, {
                        'name': data['name'],
                        'category': code,
                        'quantity': 1.0,
                        'rate': 100.0,
                        'rule': code,
                        'amount': data['amount'],
                        'sequence': sequence,
                        'payslip_run_id': run.id,
                    }))
                    sequence += 1

            _logger.info("Created summary lines: %s", summary_lines)
            run.write({'summary_line_ids': summary_lines})

class SalarySummaryLine(models.Model):
    _name = 'salary.summary.line'
    _description = 'Salary Summary Line'
    _order = 'sequence, id'

    # name = fields.Char(required=True, string='Name')
    # sequence = fields.Integer(required=True, index=True, default=5)
    # category = fields.Char(string='Category')
    # quantity = fields.Float(digits='Payroll', default=1.0)
    # rate = fields.Float(string='Rate (%)', digits='Payroll Rate', default=100.0)
    # rule = fields.Char(string='Rule')
    # amount = fields.Monetary(string='Amount')
    # total = fields.Monetary(compute='_compute_total', string='Total', store=True)
    
    # payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    # currency_id = fields.Many2one('res.currency', related='payslip_run_id.company_id.currency_id')
    # company_id = fields.Many2one('res.company', related='payslip_run_id.company_id', store=True)

    # @api.depends('quantity', 'amount', 'rate')
    # def _compute_total(self):
    #     for line in self:
    #         line.total = float(line.quantity) * line.amount * line.rate / 100

    # def get_summary_styling_dict(self):
    #     return {
    #         'NET': {
    #             'line_style': 'color:#875A7B;',
    #             'line_class': 'o_total o_border_bottom fw-bold',
    #         },
    #         'GROSS': {
    #             'line_style': 'color:#00A09D;',
    #             'line_class': 'o_subtotal o_border_bottom',
    #         },
    #         'BASIC': {
    #             'line_style': 'color:#00A09D;',
    #             'line_class': 'o_subtotal o_border_bottom',
    #         },
    #     }
    
    
    name = fields.Char(required=True, string='Name')
    sequence = fields.Integer(required=True, index=True, default=5)
    category = fields.Char(string='Category')
    quantity = fields.Float(digits='Payroll', default=1.0)
    rate = fields.Float(string='Rate (%)', digits='Payroll Rate', default=100.0)
    rule = fields.Char(string='Rule')
    amount = fields.Monetary(string='Amount')
    total = fields.Monetary(compute='_compute_total', string='Total', store=True)
    
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batch', required=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', related='payslip_run_id.company_id.currency_id')
    company_id = fields.Many2one('res.company', related='payslip_run_id.company_id', store=True)

    @api.depends('quantity', 'amount', 'rate')
    def _compute_total(self):
        for line in self:
            line.total = float(line.quantity) * line.amount * line.rate / 100