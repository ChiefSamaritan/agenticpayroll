# app/services/deductions.py

from typing import Dict, Any

ENABLE_DEDUCTION_INTEGRITY_CHECK = True


def _amount_from_rule(gross: float, rule: Dict[str, Any]) -> float:
    """
    Supports either percentage-based ('rate' + basis='gross') or fixed 'amount'.
    If 'basis' == 'annual', caller should pass a periodized amount in rule['period_amount'].
    """
    basis = rule.get("basis", "gross")
    if "amount" in rule:
        # fixed amount (per period by default)
        return float(rule["amount"])
    rate = float(rule.get("rate", 0.0))
    if basis == "gross":
        return gross * rate
    # 'annual' and other bases can be extended here; fall back to 0
    return 0.0

def _resolve_benefit_amount(gross_pay: float, cfg: dict, periods_per_year: int) -> float:
    """
    Compute a single optional benefit amount based on its config.
    Supports:
      - {"rate": 0.04, "basis": "gross"}
      - {"amount": 100, "basis": "amount"}
      - {"amount": 3000, "basis": "annual"}  # prorated
    """
    basis = cfg.get("basis", "gross")
    if "rate" in cfg and basis == "gross":
        return gross_pay * float(cfg["rate"])
    if "amount" in cfg:
        amt = float(cfg["amount"])
        if basis == "annual":
            return amt / float(periods_per_year)
        # default treat as per-period fixed amount
        return amt
    return 0.0

def calculate_deductions(employee, gross_pay: float, config: Dict[str, Any]) -> dict:
    """
    Reads the new schema:
      - config["allowance_rules"][name] = { tax_treatment: "exempt"|"taxable"|..., basis: "amount" }
      - config["statutory"]["employee_contributions"] = [ {name, rate|amount, basis, pre_tax: bool} ]
      - config["statutory"]["other_employee_deductions"] = optional extras (pre/post-tax, optional)
      - config["income_tax_brackets"] with last 'up_to' possibly null

    Pre-tax items reduce taxable income. Post-tax items do not.
    """
    allowances = employee.allowances or {}
    pre_tax_deductions = 0.0
    post_tax_deductions = 0.0
    pre_tax_breakdown: Dict[str, float] = {}
    post_tax_breakdown: Dict[str, float] = {}
    periods_per_year = int(config.get("periods_per_year", 12))

    # 1) Allowance exemptions: treat tax_treatment == "exempt" as fully exempting the allowance amount
    tax_exempt_amount = 0.0
    tax_exemptions_applied: Dict[str, float] = {}
    for name, rule in (config.get("allowance_rules") or {}).items():
        if rule.get("tax_treatment") == "exempt" and name in allowances:
            exempt = float(allowances[name])
            if exempt > 0:
                tax_exempt_amount += exempt
                tax_exemptions_applied[name] = round(exempt, 2)

    # 2) Statutory employee contributions (always applied)
    statutory = config.get("statutory", {}) or {}
    for item in statutory.get("employee_contributions", []):
        amount = _amount_from_rule(gross_pay, item)
        if amount <= 0:
            continue
        if item.get("pre_tax", False):
            pre_tax_deductions += amount
            pre_tax_breakdown[item["name"]] = round(amount, 2)
        else:
            post_tax_deductions += amount
            post_tax_breakdown[item["name"]] = round(amount, 2)

    # 3) Other employee deductions (may be optional)
    opted = getattr(employee, "benefits_opt_in", {}) or {}
    for item in statutory.get("other_employee_deductions", []):
        # If marked optional, only apply when employee opted in (by name)
        if item.get("optional", False):
            if not opted.get(item["name"], False):
                continue
        amount = _amount_from_rule(gross_pay, item)
        if amount <= 0:
            continue
        if item.get("pre_tax", False):
            pre_tax_deductions += amount
            pre_tax_breakdown[item["name"]] = round(amount, 2)
        else:
            post_tax_deductions += amount
            post_tax_breakdown[item["name"]] = round(amount, 2)

    # 4) Taxable income: gross minus allowance exemptions and ALL pre-tax deductions
    taxable_income = max(gross_pay - tax_exempt_amount - pre_tax_deductions, 0.0)

    # 5) Progressive income tax
    #    Treat up_to: null as infinity
    brackets = []
    for b in config.get("income_tax_brackets", []):
        up_to = float("inf") if b["up_to"] is None else float(b["up_to"])
        brackets.append({"up_to": up_to, "rate": float(b["rate"])})
    brackets.sort(key=lambda x: x["up_to"])

    tax_bracket_details = []
    income_tax = 0.0
    last_threshold = 0.0
    remaining = taxable_income

    for b in brackets:
        if remaining <= 0:
            break
        span = b["up_to"] - last_threshold
        if span < 0:  # guard against badly ordered brackets
            span = 0
        taxable_at_this_rate = min(remaining, span)
        if taxable_at_this_rate > 0:
            tax_for_bracket = taxable_at_this_rate * b["rate"]
            income_tax += tax_for_bracket
            tax_bracket_details.append({
                "up_to": None if b["up_to"] == float("inf") else b["up_to"],
                "rate": b["rate"],
                "amount": round(tax_for_bracket, 2),
            })
            remaining -= taxable_at_this_rate
        last_threshold = b["up_to"]
        
    # 6) Optional benefits (NEW): read from config["optional_benefits"]
    # Employee opt-ins come from employee.benefits_opt_in (preferred) or employee.opted_benefits (fallback)
    optional_benefits_cfg: Dict[str, dict] = config.get("optional_benefits", {})
    employee_optins: Dict[str, Any] = getattr(employee, "benefits_opt_in", None) or getattr(employee, "opted_benefits", {}) or {}

    for benefit_name, benefit_cfg in optional_benefits_cfg.items():
        # Skip if employee didn't opt in
        opted_value = employee_optins.get(benefit_name)
        if not opted_value:
            continue

        # If employee provided a custom amount in opt-in, allow it to override config "amount"
        # Format supported:
        #   benefits_opt_in: { "RRSP_optional": {"amount": 200, "pre_tax": true} }  OR  true
        effective_cfg = dict(benefit_cfg)
        if isinstance(opted_value, dict):
            if "amount" in opted_value:
                effective_cfg["amount"] = opted_value["amount"]
            if "rate" in opted_value:
                effective_cfg["rate"] = opted_value["rate"]
            # employee can override pre_tax flag; otherwise config governs
            pre_tax_flag = bool(opted_value.get("pre_tax", effective_cfg.get("pre_tax", False)))
        else:
            pre_tax_flag = bool(effective_cfg.get("pre_tax", False))

        amount = _resolve_benefit_amount(gross_pay, effective_cfg, periods_per_year)
        if amount <= 0:
            continue

        if pre_tax_flag:
            pre_tax_deductions += amount
            pre_tax_breakdown[benefit_name] = round(amount, 2)
        else:
            post_tax_deductions += amount
            post_tax_breakdown[benefit_name] = round(amount, 2)

    # 7) Totals
    total_pre_tax_deductions = round(pre_tax_deductions, 2)
    total_post_tax_deductions = round(post_tax_deductions, 2)

    total_deductions = (
        income_tax + total_post_tax_deductions + total_pre_tax_deductions
    )

    # 8) Integrity check
    if ENABLE_DEDUCTION_INTEGRITY_CHECK:
        computed = income_tax + total_post_tax_deductions + total_pre_tax_deductions
        assert round(total_deductions, 2) == round(computed, 2), (
            f"[Integrity Check Failed] total_deductions={total_deductions} vs computed={computed}"
        )

    return {
        "taxable_income": round(taxable_income, 2),
        "tax_exemptions_applied": tax_exemptions_applied,
        "income_tax": round(income_tax, 2),

        "pre_tax_deductions": total_pre_tax_deductions,
        "post_tax_deductions": total_post_tax_deductions,
        "total_deductions": round(total_deductions, 2),

        "tax_bracket_details": tax_bracket_details,

        # For your breakdown block
        "total_pre_tax_deductions": total_pre_tax_deductions,
        "total_post_tax_deductions": total_post_tax_deductions,
        "pre_tax_breakdown": pre_tax_breakdown,
        "post_tax_breakdown": post_tax_breakdown,
    }