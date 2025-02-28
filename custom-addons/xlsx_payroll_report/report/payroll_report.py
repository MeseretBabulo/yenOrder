from odoo import models
import string

class PayrollReport(models.AbstractModel):
    _name = 'report.xlsx_payroll_report.xlsx_payroll_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        format_header = workbook.add_format({
            'font_size': 16,
            'align': 'center',
            'bold': True,
            'font_name': 'Arial',
            'bg_color': '#36f9b0'
        })
        
        format_table_header = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'bg_color': '#bdd794',
            'font_name': 'Arial',
            'bold': True,
            'border': 1,
            'rotation': 90  
        })

        format_table_header_summary = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'bg_color': '#bdd794',
            'font_name': 'Arial',
            'bold': True,
        })

        format_table_sig = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'text_wrap': True,
            'font_name': 'Arial',
            'bold': True 
        })
        
        format_cell = workbook.add_format({
            'font_size': 11,
            'align': 'right',
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Arial'
        })
        
        format_cell_center = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'border': 1,
            'font_name': 'Arial'
        })
        
        format_total = workbook.add_format({
            'font_size': 12,
            'align': 'right',
            'bold': True,
            'border': 2,
            'num_format': '#,##0.00',
            'bg_color': '#E6E6E6',
            'font_name': 'Arial'
        })

        format_signature = workbook.add_format({
            'font_size': 11,
            'align': 'center',
            'font_name': 'Arial',
            'text_wrap': True,
        })

        sheet = workbook.add_worksheet('Payroll Register')
        
        # Increase row height for headers
        sheet.set_row(4, 150)

        # Reordered headers for better logical flow
        headers = [
            'E-ID', 
            'Full Name',
            'WORK DAY', 
            'Basic Salary',
            'Transport Allowance',
            'Telephon Allowance',
            'Over Time',
            'Total TaxableSalary',
            'Loan',
            '7%PENSION TAX EMPLY',
            '11%PENSION TAX EMPLY',
            'Income Tax',
            'Total Deductions',
            'Net Pay'
        ]

        # Adjust column widths
        sheet.set_column('A:A', 8)    # E-ID
        sheet.set_column('B:B', 27)   # Full Name
        sheet.set_column('C:C', 14)   # Work Day
        sheet.set_column('D:D', 14)   # Basic Salary
        sheet.set_column('E:F', 8)   # Allowances
        sheet.set_column('G:G', 8)   # Over Time
        sheet.set_column('H:H', 14)   # Total Taxable Salary
        sheet.set_column('I:I', 8)   # Loan
        sheet.set_column('J:J', 12)   # 7% Pension
        sheet.set_column('K:K', 12)   # 11% Pension
        sheet.set_column('L:L', 12)   # Income Tax
        sheet.set_column('M:M', 13)   # Total Deductions
        sheet.set_column('N:N', 14)   # Net Pay

        # Company header
        company_name = 'CHINAKSEN IMPORT AND EXPORT'
        payroll_text = 'PAYROLL REGISTER'
        month_text = f'FOR THE MONTH OF {lines.date_start.strftime("%B %Y")} E.C.'

        # Center headers
        sheet.merge_range('D1:K1', company_name, format_header)
        sheet.merge_range('D2:K2', payroll_text, format_header)
        sheet.merge_range('D3:K3', month_text, format_header)

        # Write headers
        for col, header in enumerate(headers):
            sheet.write(4, col, header, format_table_header)
        
        row = 5
        total_amounts = {header: 0 for header in headers[3:]}
        
        for payslip in lines.slip_ids:
            col = 0
            sheet.write(row, col, payslip.employee_id.id, format_cell_center)
            sheet.write(row, col + 1, payslip.employee_id.name, format_cell)
            sheet.write(row, col + 2, '30', format_cell_center)
            
            basic_salary = transport = taxable = overtime = 0
            for line in payslip.line_ids:
                if line.code == 'BASIC':
                    basic_salary = line.total
                elif line.code == 'TRANSPORT':
                    transport = line.total
                elif line.code == 'INCT':
                    income = -(line.total)
                elif line.code == 'GROSS':
                    taxable = line.total
                elif line.code == 'OT':
                    overtime = line.total
                elif line.code == 'NET':
                    net_pay = line.total
            
            pension_7 = basic_salary * 0.07
            pension_11 = basic_salary * 0.11
            income_tax = income
            total_deductions = pension_7  + income_tax
            net_pay = round(taxable - total_deductions,1)
            
            values = [
                basic_salary, transport, 0, overtime,
                taxable, 0, pension_7,
                pension_11, income_tax, total_deductions, net_pay
            ]
            
            for idx, value in enumerate(values):
                sheet.write(row, idx + 3, value, format_cell)
                total_amounts[headers[idx + 3]] += value
            
            row += 1
        
        # Totals row
        sheet.write(row, 0, 'TOTAL', format_total)
        for col, (header, total) in enumerate(total_amounts.items(), start=3):
            sheet.write(row, col, total, format_total)

        # Signatures section
        sig_row = row + 3
        signatures = ['PREPARED BY', 'CHECKED BY', 'APPROVED BY', 'PAID BY']
        sig_cols = [0, 4, 7, 10]
        
        for sig, col in zip(signatures, sig_cols):
            sheet.merge_range(sig_row, col, sig_row, col + 2, sig, format_table_sig)
            sheet.merge_range(sig_row + 2, col, sig_row + 2, col + 2, 'signatures: ________________', format_signature)
            sheet.merge_range(sig_row + 3, col, sig_row + 3, col + 2, 'Date: ________________', format_signature)
            
        # Account summary section
        summary_row = sig_row + 6
        sheet.merge_range(f'B{summary_row}:C{summary_row}', 'SALARY EXPENSE SUMMARY', format_table_header_summary)
        summary_items = [
            ('NET SALARY', total_amounts[headers[13]]),
            ('OVER TIME', total_amounts[headers[6]]),
            ('TRANSPORT ALLOWANCE', total_amounts[headers[4]]),
            ('TELEPHONE ALLOWANCE', 0),
            ('PENSION TAX EMPLOY 11%', total_amounts[headers[10]]),
            ('Staff Debtor-Loan', total_amounts[headers[8]]),
            ('PENSION PAYABLE 18%(7+11)', total_amounts[headers[9]]+total_amounts[headers[10]]),
            ('INCOME TAX PAYABLE', total_amounts[headers[11]]),
        ]

        curr_row = summary_row + 1
        summary_total = 0  # Initialize summary total

        for item, amount in summary_items:
            sheet.write(curr_row, 1, item, format_cell)
            sheet.write(curr_row, 2, amount, format_cell)
            if item != 'PENSION TAX EMPLOY 11%':  # Only add to total if not pension tax
                summary_total += amount
            curr_row += 1

        # Summary total
        sheet.write(curr_row, 1, 'TOTAL', format_total)
        sheet.write(curr_row, 2, summary_total, format_total)