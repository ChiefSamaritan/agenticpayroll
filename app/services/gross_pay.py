# app/services/gross_pay.py

def calculate_gross_pay(employee, config: dict):
    """
    Calculates earnings only:
      base pay (prefer monthly base if provided, else hourly * hours_worked)
      overtime pay (hourly * overtime_hours * multiplier)
      period bonuses
      allowances (sum all positive amounts; tax treatment handled elsewhere)
    Returns: gross_pay, base_pay, overtime_pay, allowances_breakdown
    """
    # Prefer a provided base salary for the period; else compute from hourly.
    base_pay_val = float(getattr(employee, "base_pay", 0) or 0)
    hourly_rate = float(getattr(employee, "hourly_rate", 0) or 0)
    hours_worked = float(getattr(employee, "hours_worked", 0) or 0)
    overtime_hours = float(getattr(employee, "overtime_hours", 0) or 0)
    bonuses = float(getattr(employee, "bonuses", 0) or 0)

    if base_pay_val > 0:
        base_pay = base_pay_val
    else:
        base_pay = hourly_rate * hours_worked

    # Configurable OT multiplier; default to 1.25 if not present
    ot_multiplier = float(config.get("overtime_multiplier", 1.25))
    overtime_pay = 0.0
    if hourly_rate > 0 and overtime_hours > 0:
        overtime_pay = hourly_rate * overtime_hours * ot_multiplier

    # Allowances: sum all positive amounts; tax treatment handled in deductions
    total_allowances = 0.0
    applicable_allowances = {}
    allowances = getattr(employee, "allowances", {}) or {}
    for name, amt in allowances.items():
        try:
            val = float(amt)
        except (TypeError, ValueError):
            continue
        if val > 0:
            applicable_allowances[name] = val
            total_allowances += val

    gross_pay = base_pay + overtime_pay + bonuses + total_allowances
    return gross_pay, base_pay, overtime_pay, applicable_allowances


def calculate_taxable_gross(gross: float, config: dict, employee):
    """
    Optional helper: if you still need a taxable-gross helper, align it to the new
    country config format that uses `allowance_rules` with tax_treatment.
    Only excludes allowances whose tax_treatment == 'exempt'.
    (Most flows should now use deductions.py as the source of truth.)
    """
    allowance_rules = config.get("allowance_rules", {}) or {}
    allowances = getattr(employee, "allowances", {}) or {}

    exempt_total = 0.0
    for name, amt in allowances.items():
        try:
            val = float(amt)
        except (TypeError, ValueError):
            continue
        rule = allowance_rules.get(name, {})
        if rule.get("tax_treatment") == "exempt" and val > 0:
            exempt_total += val

    taxable = max(gross - exempt_total, 0.0)
    return taxable, exempt_total