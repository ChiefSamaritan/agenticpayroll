from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from sqlalchemy import select, and_
from sqlalchemy.exc import DBAPIError
from datetime import date

from app.models.payroll_record import PayrollRecord
from app.models.employee import PayrollRequest
from app.config.country_config import country_config
from app.database.session import get_async_db
from app.services.deductions import calculate_deductions

from app.services.employer_costs import calculate_employer_costs
from app.services.gross_pay import calculate_gross_pay
from app.services.payslip import generate_payslip
from app.utils.security import verify_api_key
from app.models.payrun import (
    Payrun, EmployeePay, EmployeeAllowances,
    EmployerContributions, EmployeeBenefitsDeductions
)
from app.models.payrun import Employee as EmployeeORM

router = APIRouter()

def _pick_named_amount(name: str, pre_tax: dict, post_tax: dict) -> float:
    """
    Helper to populate legacy columns like social_security/health_insurance/solidarity_fund
    from the new deduction breakdowns (if present). Returns 0.0 if not found.
    """
    return float(pre_tax.get(name, 0.0)) + float(post_tax.get(name, 0.0))

@router.post("/calculate", dependencies=[Depends(verify_api_key)])
async def calculate_payroll(
    request: PayrollRequest, db: AsyncSession = Depends(get_async_db)
):
    # IDs and period inputs come from the request
    req_emp = request.employee
    company = request.company

    # 0) Load employee master record from DB (source of truth for metadata)
 
    # --- Load employee record if present; okay if missing in tests ---
    employee_db = None
    try:
        result = await db.execute(
            select(EmployeeORM).where(
                and_(
                    EmployeeORM.id == req_emp.employee_id,   # VARCHAR(50)
                    EmployeeORM.tenant_id == req_emp.tenant_id  # INT
                )
            )
        )
        employee_db = result.scalar_one_or_none()
    except Exception:
        employee_db = None
        
    #if not employee_db:
    #   raise HTTPException(status_code=404, detail="Employee not found for tenant.")

    # 1) Country config (you already have this above)
    effective_country = (employee_db.country if (employee_db and getattr(employee_db, "country", None)) else req_emp.country)
    if not effective_country:
        raise HTTPException(status_code=400, detail="Country is required.")

    config = country_config.get(effective_country)
    if not config:
        raise HTTPException(status_code=400, detail=f"Country configuration not found for {effective_country}")

    # 1a) Normalize IDs for later writes (INT/STR as per schema)
    tenant_int = int(req_emp.tenant_id)
    employee_id_str = str(req_emp.employee_id)

    # 1b) Normalize dict-like fields defensively
    allowances_map = dict(getattr(req_emp, "allowances", {}) or {})

    raw_benefits = getattr(req_emp, "benefits_opt_in", {}) or {}
    if hasattr(raw_benefits, "model_dump"):          # Pydantic v2
        benefits_map = {k: v for k, v in raw_benefits.model_dump().items() if v is not None}
    elif hasattr(raw_benefits, "dict"):               # Pydantic v1
        benefits_map = {k: v for k, v in raw_benefits.dict().items() if v is not None}
    elif isinstance(raw_benefits, dict):
        benefits_map = raw_benefits
    else:
        benefits_map = {}

    # 2) Build a lightweight object the calculators expect
    class CalcEmployee:
        # IDs & country
        tenant_id = tenant_int
        employee_id = employee_id_str
        country = effective_country

        # Prefer request → fallback to DB → else 0.0
        hourly_rate = float(
            req_emp.hourly_rate
            if getattr(req_emp, "hourly_rate", None) is not None
            else (float(getattr(employee_db, "hourly_rate", 0) or 0))
        )
        base_pay = float(
            getattr(req_emp, "base_pay", None)
            if getattr(req_emp, "base_pay", None) is not None
            else (float(getattr(employee_db, "base_pay", 0) or 0))
        )

        # Period inputs (request driven)
        hours_worked = float(getattr(req_emp, "hours_worked", 0.0) or 0.0)
        overtime_hours = float(getattr(req_emp, "overtime_hours", 0.0) or 0.0)
        bonuses = float(getattr(req_emp, "bonuses", 0.0) or 0.0)

        allowances = allowances_map
        benefits_opt_in = benefits_map

        # Metadata: request first; else DB; else None
        metadata = (
            dict(req_emp.metadata)
            if getattr(req_emp, "metadata", None)
            else {
                "full_name": getattr(employee_db, "full_name", None) if employee_db else None,
                "job_title": getattr(employee_db, "job_title", None) if employee_db else None,
                "department": getattr(employee_db, "department", None) if employee_db else None,
                "tax_id": getattr(employee_db, "tax_id", None) if employee_db else None,
                "bank_account_last4": getattr(employee_db, "bank_account_last4", None) if employee_db else None,
            }
        )

    calc_emp = CalcEmployee()

    # 3) Earnings
    gross_pay, base_pay, overtime_pay, allowances_breakdown = calculate_gross_pay(calc_emp, config)

    # 4) Employee-side deductions (statutory + optional benefits) & tax
    deductions = calculate_deductions(calc_emp, gross_pay, config)

    # 5) Net pay
    total_deductions = float(deductions["total_deductions"])
    net_pay = gross_pay - total_deductions

    # 6) Employer-side costs (statutory employer contribs + employer match of optional benefits)
    total_employer_cost, employer_contributions = calculate_employer_costs(calc_emp, gross_pay, config)

    # Derive legacy fields if present in breakdowns (they may be absent; default to 0)
    social_security = _pick_named_amount("social_security", deductions["pre_tax_breakdown"], deductions["post_tax_breakdown"])
    health_insurance = _pick_named_amount("health_insurance", deductions["pre_tax_breakdown"], deductions["post_tax_breakdown"])
    solidarity_fund = _pick_named_amount("solidarity_fund", deductions["pre_tax_breakdown"], deductions["post_tax_breakdown"])

    breakdown = {
        "base_pay": round(base_pay, 2),
        "overtime_pay": round(overtime_pay, 2),
        "bonuses": round(calc_emp.bonuses, 2),
        "allowances_breakdown": {k: round(v, 2) for k, v in allowances_breakdown.items()},
        "gross_pay": round(gross_pay, 2),

        "taxable_income": deductions["taxable_income"],
        "tax_exemptions_applied": deductions["tax_exemptions_applied"],
        "income_tax": deductions["income_tax"],

        "total_deductions": round(total_deductions, 2),
        "net_pay": round(net_pay, 2),

        "employer_costs": {k: round(v, 2) for k, v in employer_contributions.items()},
        "total_employer_cost": round(total_employer_cost, 2),

        "tax_bracket_details": deductions["tax_bracket_details"],

        # keeps UI/DB compatibility for detailed benefits breakdowns
        "benefits_deductions": {
            "pre_tax": deductions["pre_tax_breakdown"],
            "post_tax": deductions["post_tax_breakdown"],
            "total_pre_tax": deductions["total_pre_tax_deductions"],
            "total_post_tax": deductions["total_post_tax_deductions"],
        },

        # legacy fields for EmployeePay (derived above; may be zero if not configured)
        "social_security": round(social_security, 2),
        "health_insurance": round(health_insurance, 2),
        "solidarity_fund": round(solidarity_fund, 2),

        # display metadata
        "pay_period": "March 2025",
        "pay_type": "Monthly",
    }

    # 7) Generate Payslip
    payslip_path = generate_payslip(calc_emp, breakdown, net_pay, {"total_employer_cost": total_employer_cost}, company)

    # 8) Persist into Payrun / Payslip tables
    pay_period = "March 2025"
    period_start = date(2025, 3, 1)
    period_end = date(2025, 3, 31)

    # a) Get or create Payrun for (tenant, country, period)
    result = await db.execute(
        select(Payrun).where(
            and_(
                Payrun.period_start == period_start,
                Payrun.period_end == period_end,
                Payrun.tenant_id == calc_emp.tenant_id,
                Payrun.country == calc_emp.country,
            )
        )
    )
    payrun = result.scalar_one_or_none()
    if not payrun:
        payrun = Payrun(
            period_start=period_start,
            period_end=period_end,
            run_date=date.today(),
            status='draft',
            total_gross=0,
            total_net=0,
            total_tax=0,
            total_employer_cost=0,
            country=calc_emp.country,
            tenant_id=calc_emp.tenant_id
        )
        db.add(payrun)
        await db.flush()

    # b) Create EmployeePay
    employee_pay = EmployeePay(
        payrun_id=payrun.id,
        tenant_id=calc_emp.tenant_id,         # ← use calc_emp
        employee_id=calc_emp.employee_id,
        country=calc_emp.country,
        pay_period=pay_period,
        pay_type=breakdown.get("pay_type", "Monthly"),
        base_pay=breakdown["base_pay"],
        overtime_pay=breakdown["overtime_pay"],
        bonuses=breakdown["bonuses"],
        hours_worked=calc_emp.hours_worked,       # ← add
        overtime_hours=calc_emp.overtime_hours,   # ← add
        gross_pay=breakdown["gross_pay"],

        taxable_income=breakdown["taxable_income"],
        income_tax=breakdown["income_tax"],

        # legacy/statutory fields if your schema still has them
        social_security=breakdown["social_security"],
        health_insurance=breakdown["health_insurance"],
        solidarity_fund=breakdown["solidarity_fund"],

        total_deductions=breakdown["total_deductions"],
        net_pay=breakdown["net_pay"],

        total_employer_cost=breakdown["total_employer_cost"],

        total_pre_tax=breakdown["benefits_deductions"]["total_pre_tax"],
        total_post_tax=breakdown["benefits_deductions"]["total_post_tax"],

        tax_bracket_details=breakdown["tax_bracket_details"],
        tax_exemptions_applied=breakdown["tax_exemptions_applied"],

        # optional: store entire breakdown of country-specific employer items if desired
        country_specific_benefits=None,  # old field; no longer used since we unified logic
    )
    db.add(employee_pay)
    await db.flush()

    # c) Allowances
    for name, amount in breakdown["allowances_breakdown"].items():
        db.add(EmployeeAllowances(payslip_id=employee_pay.id, name=name, amount=amount))

    # d) Employer Contributions
    for name, amount in breakdown["employer_costs"].items():
        db.add(EmployerContributions(payslip_id=employee_pay.id, contribution_type=name, amount=amount))

    # e) Benefits Deductions (pre/post tax): expand dicts into rows
    for dtype in ["pre_tax", "post_tax"]:
        for bname, amt in breakdown["benefits_deductions"].get(dtype, {}).items():
            db.add(
                EmployeeBenefitsDeductions(
                    payslip_id=employee_pay.id,
                    deduction_type=dtype,
                    benefit_name=bname,
                    amount=float(amt),
                )
            )

    try:
        await db.commit()
    except DBAPIError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database connection lost during commit.")

    return {
        "net_pay": net_pay,
        "gross_pay": gross_pay,
        "total_employer_cost": total_employer_cost,
        "breakdown": breakdown,
        "payslip_url": f"/payslip/{employee_pay.id}"
    }


@router.get("/payslip/{record_id}", dependencies=[Depends(verify_api_key)])
async def get_payslip(record_id: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(PayrollRecord.__table__.select().where(PayrollRecord.id == record_id))
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    return FileResponse(record.payslip_path, media_type='application/pdf', filename="payslip.pdf")
