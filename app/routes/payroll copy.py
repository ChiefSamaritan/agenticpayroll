from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from app.models.payroll_record import PayrollRecord
from app.models.employee import PayrollRequest
from app.config.country_config import country_config
from app.database.session import get_async_db
from app.services.deductions import calculate_deductions
from app.services.benefits import calculate_country_specific_benefits
from app.services.employer_costs import calculate_employer_costs
from app.services.gross_pay import calculate_gross_pay
from app.services.payslip import generate_payslip
from app.utils.security import verify_api_key
from sqlalchemy.exc import DBAPIError
import uuid

router = APIRouter()

@router.post("/calculate", dependencies=[Depends(verify_api_key)])
async def calculate_payroll(
    request: PayrollRequest, db: AsyncSession = Depends(get_async_db)
):
    employee = request.employee
    company = request.company


    config = country_config.get(employee.country)
    print(f"Iam Looking for: {employee.country}")
    print(f"Available countries: {list(country_config.keys())}")
    if not config:
        raise HTTPException(status_code=400, detail=f"Country configuration not found for {employee.country}")

    # 1. Gross Pay and Allowances
    gross_pay, base_pay, overtime_pay, allowances_breakdown = calculate_gross_pay(employee, config)

    # 2. Deductions (with tax exemptions support)
    deductions = calculate_deductions(employee, gross_pay, config)

    # 3. Benefits
    country_benefits = calculate_country_specific_benefits(gross_pay, config)
    total_benefit_deductions = country_benefits["employee_total"]
    total_benefit_employer = country_benefits["employer_total"]

    # 4. Add benefit deductions
    total_deductions = deductions["total_deductions"] + total_benefit_deductions
    net_pay = gross_pay - total_deductions

    # 5. Employer Costs
    base_employer_cost, employer_contributions = calculate_employer_costs(gross_pay, employee.country)
    total_employer_cost = base_employer_cost + total_benefit_employer

    # 6. Build breakdown
    breakdown = {
        "base_pay": round(base_pay, 2),
        "overtime_pay": round(overtime_pay, 2),
        "allowances_breakdown": {k: round(v, 2) for k, v in allowances_breakdown.items()},
        "gross_pay": round(gross_pay, 2),
        "taxable_income": deductions["taxable_income"],
        "tax_exemptions_applied": deductions["tax_exemptions_applied"],
        "income_tax": deductions["income_tax"],
        "social_security": deductions["social_security"],
        "health_insurance": deductions["health_insurance"],
        "solidarity_fund": deductions["solidarity_fund"],
        "total_deductions": round(total_deductions, 2),
        "net_pay": round(net_pay, 2),
        "employer_costs": {k: round(v, 2) for k, v in employer_contributions.items()},
        "total_employer_cost": round(total_employer_cost, 2),
        "tax_bracket_details": deductions["tax_bracket_details"],
        "country_specific_benefits": country_benefits,
        "pay_period": "March 2025",
        "pay_type": "Monthly",
        "benefits_deductions": {
            "pre_tax": deductions["pre_tax_breakdown"],
            "post_tax": deductions["post_tax_breakdown"],
            "total_pre_tax": deductions["total_pre_tax_deductions"],
            "total_post_tax": deductions["total_post_tax_deductions"]
        }
    }

    # 7. Generate Payslip
    payslip_path = generate_payslip(employee, breakdown, net_pay, {"total_employer_cost": total_employer_cost}, company)

    # 8. Persist to payrun tables ( expad beynd the payroll_record model )
    record = PayrollRecord(
        id=str(uuid.uuid4()),
        tenant_id=employee.tenant_id,
        employee_id=employee.employee_id,
        gross_pay=gross_pay,
        net_pay=net_pay,
        total_employer_cost=total_employer_cost,
        payslip_path=payslip_path
    )
    db.add(record)
    await db.commit()
    try:
        await db.commit()
    except DBAPIError as e:
        if "ConnectionDoesNotExistError" in str(e):
         # Optionally rollback and log
          await db.rollback()
          raise HTTPException(status_code=500, detail="Database connection lost during commit.")
        raise       

    return {
        "net_pay": net_pay,
        "gross_pay": gross_pay,
        "total_employer_cost": total_employer_cost,
        "breakdown": breakdown,
        "payslip_url": f"/payslip/{record.id}"
    }


@router.get("/payslip/{record_id}", dependencies=[Depends(verify_api_key)])
async def get_payslip(record_id: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        PayrollRecord.__table__.select().where(PayrollRecord.id == record_id)
    )
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    return FileResponse(record.payslip_path, media_type='application/pdf', filename="payslip.pdf")