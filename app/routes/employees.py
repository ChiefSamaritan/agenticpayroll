from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.session import get_async_db
from app.models.employee import Employee as EmployeeModel
from app.utils.security import verify_api_key

router = APIRouter()

@router.get(
    "/employees/{tenant_id}/{employee_id}",
    dependencies=[Depends(verify_api_key)]
)
async def get_employee(tenant_id: int, employee_id: str, db: AsyncSession = Depends(get_async_db)):
    """
    Fetch a single employee by tenant + employee_id.
    Use this to verify the master data (name, country, rates, etc.)
    before calling /calculate.
    """
    result = await db.execute(
        select(EmployeeModel).where(
            and_(
                EmployeeModel.tenant_id == tenant_id,
                EmployeeModel.id == employee_id,
            )
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found for tenant.")

    # Return a clean JSON (avoid leaking sensitive data if you want)
    return {
        "id": employee.id,
        "tenant_id": employee.tenant_id,
        "full_name": employee.full_name,
        "email": employee.email,
        "job_title": employee.job_title,
        "department": employee.department,
        "country": employee.country,
        "tax_id": employee.tax_id,
        "bank_account_last4": employee.bank_account_last4,
        "hire_date": employee.hire_date,
        "termination_date": employee.termination_date,
        "status": employee.status,
        "date_of_birth": employee.date_of_birth,
        "base_pay": float(employee.base_pay or 0),
        "hourly_rate": float(employee.hourly_rate or 0),
    }