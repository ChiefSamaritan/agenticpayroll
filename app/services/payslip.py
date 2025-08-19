# app/services/payslip.py
import os
import uuid
from typing import Any, Dict
from weasyprint import HTML

from app.config.settings import settings  # if you use it elsewhere; ok to keep

def _to_dict(obj: Any) -> Dict[str, Any]:
    """Return a plain dict from Pydantic v2 (model_dump), v1 (dict), or already-dict; else {}."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    md = getattr(obj, "model_dump", None)  # Pydantic v2
    if callable(md):
        try:
            return md() or {}
        except Exception:
            pass
    d = getattr(obj, "dict", None)        # Pydantic v1
    if callable(d):
        try:
            return d() or {}
        except Exception:
            pass
    return {}

def generate_payslip(employee, breakdown: dict, net_pay: float, employer_cost: dict, company):
    # Currency symbols (fallback to $)
    currency_symbols = {
        "India": "₹", "USA": "$", "Canada": "$",
        "Spain": "€", "Ireland": "€", "Philippines": "₱", "Colombia": "$"
    }
    symbol = currency_symbols.get(getattr(employee, "country", None) or "", "$")

    # Normalize metadata and company to dicts
    meta = _to_dict(getattr(employee, "metadata", None))
    comp = _to_dict(company)

    # Safe pulls
    full_name = meta.get("full_name") or "N/A"
    bank_last4 = meta.get("bank_account_last4") or "XXXX"
    job_title = meta.get("job_title") or "N/A"
    department = meta.get("department") or "N/A"
    tax_id = meta.get("tax_id") or "N/A"
    flexer = meta.get("flexer") or "N/A"

    company_name = comp.get("company_name") or "Company"
    company_address = comp.get("address") or ""

    # Benefits (new unified breakdown)
    benefits = breakdown.get("benefits_deductions", {}) or {}
    pre_tax_map: Dict[str, float] = benefits.get("pre_tax", {}) or {}
    post_tax_map: Dict[str, float] = benefits.get("post_tax", {}) or {}
    total_pre_tax = float(benefits.get("total_pre_tax", 0.0) or 0.0)
    total_post_tax = float(benefits.get("total_post_tax", 0.0) or 0.0)

    # Begin HTML
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
    <h2>{company_name}</h2>
    <p>{company_address}</p>
    <h3>Payslip for {breakdown.get("pay_period", "N/A")}</h3>

    <table>
      <tr><td><strong>Name:</strong></td><td>{full_name}</td><td><strong>Employee ID:</strong></td><td>{getattr(employee, "employee_id", "N/A")}</td></tr>
      <tr><td><strong>Job Title:</strong></td><td>{job_title}</td><td><strong>Department:</strong></td><td>{department}</td></tr>
      <tr><td><strong>Tax ID:</strong></td><td>{tax_id}</td><td><strong>Bank Account:</strong></td><td>****{bank_last4}</td></tr>
    </table>

    <div class="section-title">Earnings</div>
    <table>
      <tr><th>Description</th><th class="right">Amount</th></tr>
      <tr><td>Base Pay</td><td class="right">{symbol}{(breakdown.get('base_pay') or 0.0):,.2f}</td></tr>
      <tr><td>Overtime</td><td class="right">{symbol}{(breakdown.get('overtime_pay') or 0.0):,.2f}</td></tr>
    """

    for k, v in (breakdown.get("allowances_breakdown") or {}).items():
        html += f"<tr><td>{k.replace('_', ' ').title()}</td><td class='right'>{symbol}{(v or 0.0):,.2f}</td></tr>"

    html += f"""
      <tr class="summary"><td>Gross Pay</td><td class="right">{symbol}{(breakdown.get('gross_pay') or 0.0):,.2f}</td></tr>
    </table>
    """

    # Taxable summary
    tax_exempt_total = sum((breakdown.get("tax_exemptions_applied") or {}).values()) if breakdown.get("tax_exemptions_applied") else 0.0
    html += f"""
    <div class="section-title">Taxable Income Summary</div>
    <table>
      <tr><td>Gross Pay</td><td class="right">{symbol}{(breakdown.get('gross_pay') or 0.0):,.2f}</td></tr>
      <tr><td>Tax-Exempt Deductions</td><td class="right">-{symbol}{tax_exempt_total:,.2f}</td></tr>
      <tr class="summary"><td>Taxable Income</td><td class="right">{symbol}{(breakdown.get('taxable_income') or 0.0):,.2f}</td></tr>
    </table>
    """

    # Tax bracket details (optional)
    tbd = breakdown.get("tax_bracket_details") or []
    if tbd:
        html += """
        <div class="section-title">Income Tax Breakdown</div>
        <table>
          <tr><th>Bracket Up To</th><th class="right">Rate</th><th class="right">Taxed Amount</th></tr>
        """
        for bracket in tbd:
            up_to = bracket.get("up_to")
            up_to_display = "∞" if up_to is None else f"{float(up_to):,.2f}"
            rate = float(bracket.get("rate") or 0.0) * 100.0
            amount = float(bracket.get("amount") or 0.0)
            html += f"<tr><td>{up_to_display}</td><td class='right'>{rate:.1f}%</td><td class='right'>{symbol}{amount:,.2f}</td></tr>"
        html += "</table>"

    # Employee deductions (income tax + pre/post benefit deductions + legacy fields)
    income_tax = float(breakdown.get("income_tax") or 0.0)
    social_security = float(breakdown.get("social_security") or 0.0)
    health_insurance = float(breakdown.get("health_insurance") or 0.0)
    solidarity_fund = float(breakdown.get("solidarity_fund") or 0.0)

    html += f"""
    <div class="section-title">Employee Deductions</div>
    <table>
      <tr><th>Description</th><th class="right">Amount</th></tr>
      <tr><td>Income Tax</td><td class='right'>-{symbol}{income_tax:,.2f}</td></tr>
    """

    # Pre-tax benefit deductions
    for k, v in pre_tax_map.items():
        amt = float(v or 0.0)
        html += f"<tr><td>{k.replace('_',' ').title()} (Pre‑Tax)</td><td class='right'>-{symbol}{amt:,.2f}</td></tr>"

    # Post-tax benefit deductions
    for k, v in post_tax_map.items():
        amt = float(v or 0.0)
        html += f"<tr><td>{k.replace('_',' ').title()} (Post‑Tax)</td><td class='right'>-{symbol}{amt:,.2f}</td></tr>"

    # Legacy lines if you still store them
    if social_security:
        html += f"<tr><td>Social Security</td><td class='right'>-{symbol}{social_security:,.2f}</td></tr>"
    if health_insurance:
        html += f"<tr><td>Health Insurance</td><td class='right'>-{symbol}{health_insurance:,.2f}</td></tr>"
    if solidarity_fund:
        html += f"<tr><td>Solidarity Fund</td><td class='right'>-{symbol}{solidarity_fund:,.2f}</td></tr>"

    total_employee_deductions = float(breakdown.get("total_deductions") or 0.0)
    html += f"""
      <tr class="summary"><td>Total Employee Deductions</td><td class="right">-{symbol}{total_employee_deductions:,.2f}</td></tr>
    </table>
    """

    # Employer contributions (from employer_costs)
    html += f"""
    <div class="section-title">Employer Contributions</div>
    <table>
      <tr><th>Description</th><th class="right">Amount</th></tr>
    """
    employer_costs = breakdown.get("employer_costs") or {}
    total_employer_contrib = 0.0
    for k, v in employer_costs.items():
        amt = float(v or 0.0)
        html += f"<tr><td>{k.replace('_',' ').title()}</td><td class='right'>{symbol}{amt:,.2f}</td></tr>"
        total_employer_contrib += amt
    html += f"""
      <tr class="summary"><td>Total Employer Contribution</td><td class="right">{symbol}{total_employer_contrib:,.2f}</td></tr>
    </table>
    """

    # Summary
    html += f"""
    <div class="section-title">Summary</div>
    <table>
      <tr><td>Gross Pay</td><td class="right">{symbol}{(breakdown.get('gross_pay') or 0.0):,.2f}</td></tr>
      <tr><td>Total Deductions</td><td class="right">-{symbol}{(breakdown.get('total_deductions') or 0.0):,.2f}</td></tr>
      <tr class="summary"><td>Net Pay</td><td class="right">{symbol}{(net_pay or 0.0):,.2f}</td></tr>
    </table>

    <div class="footer">This is a computer-generated payslip. Flexer: {flexer}</div>
    </body></html>
    """

    # Write PDF
    file_path = f"payslips/{uuid.uuid4()}.pdf"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    HTML(string=html).write_pdf(file_path)
    return file_path