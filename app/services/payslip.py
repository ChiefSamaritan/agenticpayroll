import os
import uuid
from weasyprint import HTML
from app.models.employee import Employee, CompanyMetadata
from app.config.settings import settings

def generate_payslip(employee: Employee, breakdown: dict, net_pay: float, employer_cost: dict, company: CompanyMetadata):
    currency_symbols = {
        "India": "₹", "USA": "$", "Canada": "$",
        "Spain": "€", "Ireland": "€", "Philippines": "₱", "Colombia": "$"
    }
    symbol = currency_symbols.get(employee.country, "$")

    meta = employee.metadata.dict() if employee.metadata else {}
    full_name = meta.get("full_name", "N/A")
    bank_last4 = meta.get("bank_account_last4", "XXXX")
    job_title = meta.get("job_title", "N/A")
    department = meta.get("department", "N/A")
    tax_id = meta.get("tax_id", "N/A")
    flexer = meta.get("flexer", "N/A")

    html = f"""
    <html><head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; }}
        th {{ background-color: #f0f0f0; }}
        .right {{ text-align: right; }}
        .section-title {{ font-size: 16px; margin-top: 30px; }}
        .summary {{ font-weight: bold; background-color: #eee; }}
        .footer {{ font-size: 12px; color: #666; margin-top: 40px; }}
    </style>
    </head><body>
    <h2>{company.company_name or 'Company'}</h2>
    <p>{company.address or ''}</p>
    <h3>Payslip for {breakdown.get("pay_period", "N/A")}</h3>

    <table>
      <tr><td><strong>Name:</strong></td><td>{full_name}</td><td><strong>Employee ID:</strong></td><td>{employee.employee_id}</td></tr>
      <tr><td><strong>Job Title:</strong></td><td>{job_title}</td><td><strong>Department:</strong></td><td>{department}</td></tr>
      <tr><td><strong>Tax ID:</strong></td><td>{tax_id}</td><td><strong>Bank Account:</strong></td><td>****{bank_last4}</td></tr>
    </table>

    <div class="section-title">Earnings</div>
    <table>
      <tr><th>Description</th><th class="right">Amount</th></tr>
      <tr><td>Base Pay</td><td class="right">{symbol}{breakdown['base_pay']:,.2f}</td></tr>
      <tr><td>Overtime</td><td class="right">{symbol}{breakdown['overtime_pay']:,.2f}</td></tr>
    """

    for k, v in breakdown.get("allowances_breakdown", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{v:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Gross Pay</td><td class="right">{symbol}{breakdown['gross_pay']:,.2f}</td></tr>
    </table>
    """

    tax_exempt_total = sum(breakdown.get("tax_exemptions_applied", {}).values())
    html += f"""
    <div class="section-title">Taxable Income Summary</div>
    <table>
      <tr><td>Gross Pay</td><td class="right">{symbol}{breakdown['gross_pay']:,.2f}</td></tr>
      <tr><td>Tax-Exempt Deductions</td><td class="right">-{symbol}{tax_exempt_total:,.2f}</td></tr>
      <tr class="summary"><td>Taxable Income</td><td class="right">{symbol}{breakdown['taxable_income']:,.2f}</td></tr>
    </table>
    """

    if "tax_bracket_details" in breakdown:
        html += """
        <div class="section-title">Income Tax Breakdown</div>
        <table>
          <tr><th>Bracket Up To</th><th class="right">Rate</th><th class="right">Taxed Amount</th></tr>
        """
        for bracket in breakdown["tax_bracket_details"]:
            html += f"<tr><td>{bracket['up_to']:,.2f}</td><td class='right'>{bracket['rate'] * 100:.1f}%</td><td class='right'>{symbol}{bracket['amount']:,.2f}</td></tr>"
        html += "</table>"
    
    # Pre-tax country-specific benefits
    html += f"""
    <div class="section-title">Country-Specific Pre-Tax Deductions</div>
    <table>
    """
    total_pre_tax = 0.0
    for k, v in breakdown["country_specific_benefits"].get("employee_breakdown", {}).items():
        if isinstance(v, dict) and v.get("pre_tax") is True:
            amount = v.get("amount", 0.0)
            html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>-{symbol}{amount:,.2f}</td></tr>"
            total_pre_tax += amount
    html += f"""
      <tr class="summary"><td>Total Pre-Tax Deductions</td><td class='right'>-{symbol}{total_pre_tax:,.2f}</td></tr>
    </table>
    """


     # Combined Employee Deductions
    html += f"""
    <div class="section-title">Employee Deductions</div>
    <table>
    """
    total_employee_deductions = breakdown['income_tax'] + breakdown['social_security'] + breakdown['health_insurance']

    html += f"<tr><td>Income Tax</td><td class='right'>-{symbol}{breakdown['income_tax']:,.2f}</td></tr>"
    html += f"<tr><td>Social Security</td><td class='right'>-{symbol}{breakdown['social_security']:,.2f}</td></tr>"
    html += f"<tr><td>Health Insurance</td><td class='right'>-{symbol}{breakdown['health_insurance']:,.2f}</td></tr>"

    if "solidarity_fund" in breakdown:
        html += f"<tr><td>Solidarity Fund</td><td class='right'>-{symbol}{breakdown['solidarity_fund']:,.2f}</td></tr>"
        total_employee_deductions += breakdown['solidarity_fund']

    for k, v in breakdown["country_specific_benefits"].get("employee_breakdown", {}).items():
        amount = v.get("amount") if isinstance(v, dict) else v
        tax_type = "Pre-Tax" if v.get("pre_tax") else "Post-Tax"
        if isinstance(amount, (int, float)):
            html += f"<tr><td>{k.replace('_', ' ').title()} ({tax_type})</td><td class='right'>-{symbol}{amount:,.2f}</td></tr>"
            total_employee_deductions += amount
        else:
            html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>Invalid format</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Employee Deductions</td><td class="right">-{symbol}{total_employee_deductions:,.2f}</td></tr>
    </table>
    """

    # Employer contributions and benefit contributions combined
    html += f"""
    <div class="section-title">Employer Contributions</div>
    <table>
    """
    total_employer_contribution = 0.0
    for k, v in breakdown.get("employer_costs", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{v:,.2f}</td></tr>"
        total_employer_contribution += v

    for k, v in breakdown["country_specific_benefits"].get("employer_breakdown", {}).items():
        amount = v.get("amount") if isinstance(v, dict) else v
        if isinstance(amount, (int, float)):
            html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{amount:,.2f}</td></tr>"
            total_employer_contribution += amount
        else:
            html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>Invalid format</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Employer Contribution</td><td class="right">{symbol}{total_employer_contribution:,.2f}</td></tr>
    </table>
    """
    
    # Summary
    html += f"""
    <div class="section-title">Summary</div>
    <table>
      <tr><td>Gross Pay</td><td class="right">{symbol}{breakdown['gross_pay']:,.2f}</td></tr>
      <tr><td>Total Deductions</td><td class="right">-{symbol}{breakdown['total_deductions']:,.2f}</td></tr>
      <tr class="summary"><td>Net Pay</td><td class="right">{symbol}{net_pay:,.2f}</td></tr>
    </table>

    <div class="footer">This is a computer-generated payslip. Flexer: {flexer}</div>
    </body></html>
    """
    
    file_path = f"payslips/{uuid.uuid4()}.pdf"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    HTML(string=html).write_pdf(file_path)
    return file_path

