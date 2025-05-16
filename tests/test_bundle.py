import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app.main import app
import json

# Load your employee test data
with open("tests/test_employees_bundle.json") as f:
    test_employees = json.load(f)

headers = {
    "Content-Type": "application/json",
    "x-api-key": "supersecretkey"  # your real API key
}

@pytest.mark.asyncio
@pytest.mark.parametrize("employee_data", test_employees)
async def test_payroll_bundle(employee_data):
    async with AsyncClient(base_url="http://testserver") as ac:
        response = await ac.post("http://localhost:8000/calculate", json=employee_data, headers=headers)

    assert response.status_code == 200, f"Failed for {employee_data['employee']['country']}"
    result = response.json()

    assert result["gross_pay"] > 0
    assert result["net_pay"] > 0
    assert result["total_employer_cost"] >= 0