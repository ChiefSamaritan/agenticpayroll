# app/services/deductions.py

from typing import Dict, Any

ENABLE_DEDUCTION_INTEGRITY_CHECK = True


def calculate_deductions(employee, gross_pay: float, config: Dict[str, Any]) -> dict:
    allowances = employee.allowances or {}
    tax_exemptions = config.get("tax_exemptions", {})
    country = employee.country
    pre_tax_deductions = 0.0
    post_tax_deductions = 0.0
    pre_tax_breakdown = {}
    post_tax_breakdown = {}
    
    # 1. Compute tax-exempt amount
    tax_exempt_amount = 0.0
    tax_exemptions_applied = {}
    for name, rule in tax_exemptions.items():
        if name in allowances:
            if rule["type"] == "fixed":
                exempt = min(allowances[name], rule["amount"])
            elif rule["type"] == "percentage":
                exempt = gross_pay * rule["rate"]
            else:
                exempt = 0.0
            tax_exempt_amount += exempt
            tax_exemptions_applied[name] = round(exempt, 2)

    # 2. Compute taxable income
    taxable_income = max(gross_pay - tax_exempt_amount, 0)

    # 3. Income Tax (progressive)
    tax_bracket_details = []
    income_tax = 0.0
    remaining_income = taxable_income
    last_threshold = 0.0

    for bracket in config["income_tax_brackets"]:
        threshold = bracket["up_to"]
        rate = bracket["rate"]
        if remaining_income <= 0:
            break
        taxable_at_this_rate = min(remaining_income, threshold - last_threshold)
        if taxable_at_this_rate > 0:
            tax_for_bracket = taxable_at_this_rate * rate
            income_tax += tax_for_bracket
            tax_bracket_details.append({
                "up_to": threshold,
                "rate": rate,
                "amount": round(tax_for_bracket, 2)
            })
            remaining_income -= taxable_at_this_rate
        last_threshold = threshold

    # 4. Standard deductions
    social_security = gross_pay * config.get("social_security_rate", 0)
    health_insurance = gross_pay * config.get("health_insurance_rate", 0)
    solidarity_fund = gross_pay * config.get("solidarity_fund_rate", 0)

    # 5. Pre and Post-tax deductions (optional benefits)
  
    optional_benefits = config.get("benefits_opt_in_options", {})
    employee_benefits = getattr(employee, "opted_benefits", {})

    for benefit_name, benefit_config in optional_benefits.items():
        if benefit_name in employee_benefits:
            value = employee_benefits[benefit_name]
            if "employee_rate" in benefit_config:
                amount = gross_pay * benefit_config["employee_rate"]
            elif "employee_fixed" in benefit_config:
                amount = benefit_config["employee_fixed"]
            else:
                amount = 0.0

            if employee_benefits[benefit_name].get("pre_tax", False):
                pre_tax_deductions += amount
                pre_tax_breakdown[benefit_name] = round(amount, 2)
        
            else:
                post_tax_deductions += amount
                post_tax_breakdown[benefit_name] = round(amount, 2)
             

    total_pre_tax_deductions = round(pre_tax_deductions, 2)
    total_post_tax_deductions = round(post_tax_deductions, 2)

    # 6. Total deductions
    total_deductions = (
        income_tax + social_security + health_insurance + solidarity_fund +
        total_pre_tax_deductions + total_post_tax_deductions
    )

    # 7. Optional Integrity Check
    if ENABLE_DEDUCTION_INTEGRITY_CHECK:
        computed_total = (
            income_tax + social_security + health_insurance + solidarity_fund +
            total_pre_tax_deductions + total_post_tax_deductions
        )
        assert round(total_deductions, 2) == round(computed_total, 2), (
            f"[Integrity Check Failed] total_deductions: {total_deductions} != sum of components: {computed_total}"
        )

    return {
        "taxable_income": round(taxable_income, 2),
        "tax_exemptions_applied": tax_exemptions_applied,
        "income_tax": round(income_tax, 2),
        "social_security": round(social_security, 2),
        "health_insurance": round(health_insurance, 2),
        "solidarity_fund": round(solidarity_fund, 2),
        "pre_tax_deductions": total_pre_tax_deductions,
        "post_tax_deductions": total_post_tax_deductions,
        "total_deductions": round(total_deductions, 2),
        "tax_bracket_details": tax_bracket_details,
        "total_pre_tax_deductions": total_pre_tax_deductions,
        "total_post_tax_deductions": total_post_tax_deductions,
        "pre_tax_breakdown": pre_tax_breakdown,
        "post_tax_breakdown": post_tax_breakdown
    }