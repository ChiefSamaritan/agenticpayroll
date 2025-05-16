from app.config.settings import country_config

def calculate_employer_costs(gross_pay: float, country: str):
    employer_contributions = country_config.get(country, {}).get("employer_contributions", {})
    employer_costs = {k: gross_pay * v for k, v in employer_contributions.items()}
    total_employer_cost = sum(employer_costs.values())
    return total_employer_cost, employer_costs