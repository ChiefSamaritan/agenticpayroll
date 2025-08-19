def calculate_country_specific_benefits(
    gross_pay: float,
    config: dict,
    opted_in_benefits: list = None
):
    """ Optional benefits are deductions or contributions — amounts the employee agrees to pay for extra perks 
    -   (e.g., private medical, gym membership, retirement plan top-up).
    -   Employee contributions reduce net pay and are stored in employee.benefits_opt_in (or whatever field you’ve defined)
	-	Optional benefits → reduce net pay and are stored in employee.benefits_opt_in (or whatever field you’ve defined)
    """
    employee_deductions = {}
    employer_contributions = {}

    opted_in_benefits = opted_in_benefits or []

    # Initialize totals
    total_employee_pre_tax = 0.0
    total_employee_post_tax = 0.0
    total_employer_pre_tax = 0.0
    total_employer_post_tax = 0.0

    # --- Process country-specific benefits ---
    for benefit in config.get("country_specific_benefits", []):
        name = benefit["name"]

        # Employee
        if "employee_rate" in benefit:
            amount = gross_pay * benefit["employee_rate"]
            pre_tax = True  # Assume system-defined, not marked
            employee_deductions[name] = {
                "amount": round(amount, 2),
                "pre_tax": pre_tax
            }
            total_employee_pre_tax += amount  # Assume mandatory benefits are pre-tax

        # Employer
        if "employer_rate" in benefit:
            amount = gross_pay * benefit["employer_rate"]
            employer_contributions[name] = {
                "amount": round(amount, 2),
                "pre_tax": True  # Employer contributions are always pre-tax for employer
            }
            total_employer_pre_tax += amount

    # --- Process optional opted-in benefits ---
    for benefit_name in opted_in_benefits:
        benefit_config = config.get("benefits_opt_in_options", {}).get(benefit_name)
        if not benefit_config:
            continue

        # --- Employee Side ---
        pre_tax_flag = benefit_config.get("pre_tax", False)
        if "employee_rate" in benefit_config:
            amount = gross_pay * benefit_config["employee_rate"]
        else:
            amount = benefit_config.get("employee_fixed", 0)

        employee_deductions[benefit_name] = {
            "amount": round(amount, 2),
            "pre_tax": pre_tax_flag
        }

        if pre_tax_flag:
            total_employee_pre_tax += amount
        else:
            total_employee_post_tax += amount

        # --- Employer Side ---
        if "employer_rate" in benefit_config:
            amount = gross_pay * benefit_config["employer_rate"]
        else:
            amount = benefit_config.get("employer_fixed", 0)

        employer_contributions[benefit_name] = {
            "amount": round(amount, 2),
            "pre_tax": True  # Employer contributions are always pre-tax
        }
        total_employer_pre_tax += amount

    # Totals
    total_employee = total_employee_pre_tax + total_employee_post_tax
    total_employer = total_employer_pre_tax + total_employer_post_tax

    return {
        "employee_total": round(total_employee, 2),
        "employer_total": round(total_employer, 2),
        "employee_pre_tax_total": round(total_employee_pre_tax, 2),
        "employee_post_tax_total": round(total_employee_post_tax, 2),
        "employer_pre_tax_total": round(total_employer_pre_tax, 2),
        "employer_post_tax_total": round(total_employer_post_tax, 2),  # should remain 0 in most systems
        "employee_breakdown": employee_deductions,
        "employer_breakdown": employer_contributions
    }