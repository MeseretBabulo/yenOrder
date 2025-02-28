# -*- coding: utf-8 -*-
{
    'name': "Payroll Reports",
    'website': "",
    'category': 'Uncategorized',
    'Author': 'mesi2640@gmail.com',
    'version': '0.1',
    'sequence': 1,
    'depends': ['base', 'hr','hr_payroll'],
    'data': [
        'data/cron.xml',
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_view.xml',
        'views/templates.xml',
        'views/hr_payslip_run.xml',
        'views/views.xml',
        'report/report.xml',
        'report/bank_report_template.xml',
    ],
    'license': 'AGPL-3',
    'installable': True
}
