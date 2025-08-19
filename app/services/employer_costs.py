# app/services/employer_costs.py

from typing import Dict, Any, Tuple


def _prorate_if_annual(amount: float, basis: str, periods_per_year: int) -> float:
    if basis == "annual":
        return amount / float(periods_per_year)
    return amount


def _apply_caps(amount: float, rule: Dict[str, Any], periods_per_year: int) -> float:
    """
    Supports:
      - max_amount: per-period cap
      - annual_cap: cap for annualized amount (then prorated back to period)
    """
    if amount <= 0:
        return 0.0

    # Per-period cap
    if "max_amount" in rule:
        try:
            max_amt = float(rule["max_amount"])
            amount = min(amount, max_amt)
        except (TypeError, ValueError):
            pass

    # Annual cap -> convert amount to annual, cap, then prorate back to period
    if "annual_cap" in rule:
        try:
            annual_cap = float(rule["annual_cap"])
            annualized = amount * float(periods_per_year)
            if annualized > annual_cap:
                annualized = annual_cap
            amount = annualized / float(periods_per_year)
        except (TypeError, ValueError):
            pass

    return amount


def _amount_from_rule_for_employer(
    gross: float,
    rule: Dict[str, Any],
    periods_per_year: int,
) -> float:
    """
    Employer-side calculator:
      - Percentage: {"rate": 0.05, "basis": "gross"|"annual"}
      - Fixed: {"amount": 100, "basis": "per_period"| "annual"}  # per_period is default if omitted
      - Caps: "max_amount", "annual_cap"
    """
    basis = rule.get("basis", "gross")

    if "amount" in rule:
        try:
            amt = float(rule["amount"])
        except (TypeError, ValueError):
            return 0.0
        amt = _prorate_if_annual(amt, basis, periods_per_year)
        return _apply_caps(amt, rule, periods_per_year)

    # percentage path
    try:
        rate = float(rule.get("rate", 0.0))
    except (TypeError, ValueError):
        rate = 0.0

    if basis == "annual":
        # rate applies to annualized gross, then prorate
        amt = (gross * float(periods_per_year)) * rate
        amt = amt / float(periods_per_year)
    else:
        # default is rate on per-period gross
        amt = gross * rate

    return _apply_caps(amt, rule, periods_per_year)


def calculate_employer_costs(
    employee,
    gross_pay: float,
    config: Dict[str, Any],
) -> Tuple[float, Dict[str, float]]:
    """
    Employer perspective only. Does not affect net pay.

    Reads:
      - config["statutory"]["employer_contributions"]:
          [
            {
              "name": "Employer Social Security",
              "rate": 0.085,             # or "amount": 120
              "basis": "gross"|"annual", # default "gross"
              "max_amount": 500,         # optional per-period cap
              "annual_cap": 6000,        # optional annual cap (prorated)
              "display_name": "Employer SS"  # optional override for label
            },
            ...
          ]

      - config["optional_benefits"][<benefit>]:
          {
            # employer component is applied only if employee opted in
            "employer_rate": 0.04,                 # or "employer_amount": 50
            "employer_basis": "gross"|"annual",    # default "gross"
            "employer_max_amount": 200,            # optional per-period cap
            "employer_annual_cap": 2400,           # optional annual cap
            "employer_display_name": "Employer RRSP Match"  # optional label
          }

    Returns:
      total_employer_cost (float), breakdown (Dict[str, float])
    """
    breakdown: Dict[str, float] = {}
    total = 0.0
    periods_per_year = int(config.get("periods_per_year", 12))

    # 1) Statutory employer contributions
    statutory = (config.get("statutory") or {})
    for item in statutory.get("employer_contributions", []):
        amt = _amount_from_rule_for_employer(gross_pay, item, periods_per_year)
        if amt > 0:
            label = item.get("display_name") or item.get("name") or "Employer Contribution"
            val = round(amt, 2)
            breakdown[label] = val
            total += val

    # 2) Employer component for optional benefits (only if employee opted in)
    optional_cfg: Dict[str, Any] = config.get("optional_benefits", {}) or {}
    employee_optins: Dict[str, Any] = (
        getattr(employee, "benefits_opt_in", None)
        or getattr(employee, "opted_benefits", {})
        or {}
    )

    for benefit_name, cfg in optional_cfg.items():
        if not employee_optins.get(benefit_name):
            continue  # not opted in by the employee

        # Build employer rule on the fly from employer_* keys
        has_amount = "employer_amount" in cfg
        has_rate = "employer_rate" in cfg
        if not (has_amount or has_rate):
            continue  # no employer side

        emp_rule: Dict[str, Any] = {}
        if has_amount:
            emp_rule["amount"] = cfg["employer_amount"]
        if has_rate:
            emp_rule["rate"] = cfg["employer_rate"]
        emp_rule["basis"] = cfg.get("employer_basis", "gross")

        # Support caps on employer match
        if "employer_max_amount" in cfg:
            emp_rule["max_amount"] = cfg["employer_max_amount"]
        if "employer_annual_cap" in cfg:
            emp_rule["annual_cap"] = cfg["employer_annual_cap"]

        amt = _amount_from_rule_for_employer(gross_pay, emp_rule, periods_per_year)
        if amt > 0:
            label = cfg.get("employer_display_name") or f"Employer {benefit_name}"
            val = round(amt, 2)
            breakdown[label] = val
            total += val

    return round(total, 2), {k: round(v, 2) for k, v in breakdown.items()}