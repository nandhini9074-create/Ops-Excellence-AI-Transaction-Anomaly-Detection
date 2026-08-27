import pandas as pd
import json
import uuid
import random
from datetime import datetime, timezone

def generate_tx(merchant_id, outlet_id, amount, dt, merchant_name, outlet_name):
    return {
        "transaction_id": str(uuid.uuid4()),
        "transaction_no": f"TXN-{random.randint(100000, 999999)}",
        "outlet_id": str(outlet_id),
        "merchant_id": str(merchant_id),
        "profile_id": str(uuid.uuid4()),
        "transaction_timestamp": dt.isoformat(),
        "txn_date": dt.date().isoformat(),
        "txn_hour": str(dt.hour),
        "transaction_amount": round(amount, 2),
        "card_scheme": "VISA",
        "merchant_name": merchant_name,
        "outlet_name": outlet_name
    }

def main():
    # Read unique outlets from CSV
    df = pd.read_csv('my_transactions.csv')
    outlets = df[['merchant_id', 'outlet_id', 'merchant_name', 'outlet_name']].drop_duplicates().to_dict('records')
    
    # Pick 10 random outlets
    if len(outlets) > 10:
        selected_outlets = random.sample(outlets, 10)
    else:
        selected_outlets = outlets
        
    transactions = []
    now = datetime.now(timezone.utc)
    
    for i, outlet in enumerate(selected_outlets):
        if i % 2 == 0:
            # Scenario A: Z-Score (Amount Spike) -> Massive amount during normal hours
            dt = now.replace(hour=14, minute=random.randint(0, 59), second=0)
            amount = 85000.0 + random.uniform(1000, 5000)
        else:
            # Scenario B: Isolation Forest (Pattern Break) -> Normal amount but weird hour (e.g. 3 AM)
            dt = now.replace(hour=3, minute=random.randint(0, 59), second=0)
            amount = random.uniform(5.0, 50.0)
            
        transactions.append(generate_tx(
            outlet['merchant_id'], 
            outlet['outlet_id'], 
            amount, 
            dt, 
            outlet['merchant_name'], 
            outlet['outlet_name']
        ))

    with open("multi_algo_scenarios.json", "w") as f:
        json.dump(transactions, f, indent=2)

    print(f"Generated {len(transactions)} scenarios for {len(selected_outlets)} outlets in multi_algo_scenarios.json")

if __name__ == "__main__":
    main()
