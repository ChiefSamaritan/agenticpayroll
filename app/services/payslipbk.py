
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
      <tr><td>Bonuses</td><td class="right">{symbol}{employee.bonuses:,.2f}</td></tr>
    """

    for k, v in breakdown.get("allowances_breakdown", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{v:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Gross Pay</td><td class="right">{symbol}{breakdown['gross_pay']:,.2f}</td></tr>
    </table>
    """

    # Pre-tax deductions
    html += f"""
    <div class="section-title">Pre-Tax Deductions</div>
    <table>
    """

    for label, amount in breakdown.get("benefits_deductions", {}).get("pre_tax", {}).items():
        pretty = label.replace("_", " ").title()
        html += f"<tr><td>{pretty}</td><td class='right'>{symbol}{amount:,.2f}</td></tr>"

    html += f"</table>"

    # Post-tax deductions
    html += f"""
    <div class="section-title">Post-Tax Deductions</div>
    <table>
    """

    for label, amount in breakdown.get("benefits_deductions", {}).get("post_tax", {}).items():
        pretty = label.replace("_", " ").title()
        html += f"<tr><td>{pretty}</td><td class='right'>{symbol}{amount:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Deductions</td><td class="right">{symbol}{breakdown['total_deductions']:,.2f}</td></tr>
    </table>
    """
    # Statutory Taxes
    html += f"""
    <div class="section-title">Statutory Tax Deductions</div>
    <table>
      <tr><td>Income Tax</td><td class="right">-{symbol}{breakdown['income_tax']:,.2f}</td></tr>
      <tr><td>Social Security</td><td class="right">-{symbol}{breakdown['social_security']:,.2f}</td></tr>
      <tr><td>Health Insurance</td><td class="right">-{symbol}{breakdown['health_insurance']:,.2f}</td></tr>
    """

    if "solidarity_fund" in breakdown:
        html += f"<tr><td>Solidarity Fund</td><td class='right'>-{symbol}{breakdown['solidarity_fund']:,.2f}</td></tr>"

    html += "</table>"
    
    # Country-Specific Benefit Deductions (Employee)
    html += f"""
    <div class="section-title">Employee Benefit Deductions</div>
    <table>
    """

    for k, v in breakdown["country_specific_benefits"].get("employee_breakdown", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>-{symbol}{v:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Employee Benefits</td><td class="right">-{symbol}{breakdown['country_specific_benefits']['employee_total']:,.2f}</td></tr>
    </table>
    """
    # Consolidated Deductions Section
    html += f"""
    <div class="section-title">Deductions - Type A</div>
    <table>
      <tr><th>Description</th><th class="right">Amount</th></tr>

      <!-- Statutory Taxes -->
      <tr><td>Income Tax</td><td class="right">-{symbol}{breakdown['income_tax']:,.2f}</td></tr>
      <tr><td>Social Security</td><td class="right">-{symbol}{breakdown['social_security']:,.2f}</td></tr>
      <tr><td>Health Insurance</td><td class="right">-{symbol}{breakdown['health_insurance']:,.2f}</td></tr>
    """

    if "solidarity_fund" in breakdown:
        html += f"<tr><td>Solidarity Fund</td><td class='right'>-{symbol}{breakdown['solidarity_fund']:,.2f}</td></tr>"

    # Pre-tax deductions
    for label, amount in breakdown.get("benefits_deductions", {}).get("pre_tax", {}).items():
        pretty = label.replace("_", " ").title()
        html += f"<tr><td>{pretty} (Pre-Tax)</td><td class='right'>-{symbol}{amount:,.2f}</td></tr>"

    # Post-tax deductions
    for label, amount in breakdown.get("benefits_deductions", {}).get("post_tax", {}).items():
        pretty = label.replace("_", " ").title()
        html += f"<tr><td>{pretty} (Post-Tax)</td><td class='right'>-{symbol}{amount:,.2f}</td></tr>"

    # Country-specific employee deductions (like CPP, Medicare)
    for label, amount in breakdown.get("country_specific_benefits", {}).get("employee_breakdown", {}).items():
        pretty = label.replace("_", " ").title()
        html += f"<tr><td>{pretty}</td><td class='right'>-{symbol}{amount:,.2f}</td></tr>"

    # Total line
    html += f"""
      <tr class="summary"><td>Total Deductions</td><td class="right">-{symbol}{breakdown['total_deductions']:,.2f}</td></tr>
    </table>
    """
    # Employer Contributions
    html += f"""
    <div class="section-title">Employer Contributions</div>
    <table>
    """

    for k, v in breakdown.get("employer_costs", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{v:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Employer Cost</td><td class="right">{symbol}{employer_cost['total_employer_cost']:,.2f}</td></tr>
    </table>
    """
 

    # Country-Specific Employer Contributions (Dynamic from Config)
    html += f"""
    <div class="section-title">Employer Benefit Contributions</div>
    <table>
    """

    for k, v in breakdown["country_specific_benefits"].get("employer_breakdown", {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{v:,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Total Employer Cost</td><td class="right">{symbol}{breakdown['country_specific_benefits']['employer_total']:,.2f}</td></tr>
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