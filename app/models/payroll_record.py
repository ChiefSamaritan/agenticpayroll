from sqlalchemy import Column, String, Float
from app.database.connection import Base

class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    employee_id = Column(String)
    gross_pay = Column(Float)
    net_pay = Column(Float)
    total_employer_cost = Column(Float)
    payslip_path = Column(String)