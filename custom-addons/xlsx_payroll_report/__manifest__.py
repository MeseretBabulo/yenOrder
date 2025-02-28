
{
    "name": "Exxxcel Payroll Report",
    "summary": "A payroll report in xlsx format",
    'version': '17.0.1.0.0',
    "author": "AG",
    'Author': 'mesi2640@gmail.com',
    "license": "LGPL-3",
    "category": "Human Resources/Payroll",
    "depends": ['hr_payroll','report_xlsx'],
    "data": [
        'security/ir.model.access.csv',
        'views/payslip_extend_view.xml',
        'report/payroll_report.xml',
    ],
    "images": [
        'images/main_screenshot.png'
        ],
    "installable": True,
}