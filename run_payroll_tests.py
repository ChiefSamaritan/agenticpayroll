import requests
import json

API_KEY = "supersecretkey"
API_URL = "http://localhost:8000/calculate"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

with open("test_employees_bundle.json") as file:
    employees = json.load(file)

for idx, employee_record in enumerate(employees, 1):
    response = requests.post(API_URL, headers=HEADERS, json=employee_record)

    print(f"\nTest Case {idx}: {employee_record['employee']['employee_id']} from {employee_record['employee']['country']}")
    
          
    if response.status_code == 200:
        data = response.json()
        print(f"  Gross Pay: {data['gross_pay']}")
        print(f"  Net Pay:   {data['net_pay']}")
        print(f"  Employer Cost: {data['total_employer_cost']}")
        print(f"  Payslip URL: {data['payslip_url']}")
    else:
        print(f"  ❌ Error {response.status_code}: {response.text}")