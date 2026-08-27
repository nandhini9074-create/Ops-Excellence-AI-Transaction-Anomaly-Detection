import json
import uuid
import random
from datetime import datetime, timedelta, timezone

def generate_tx(merchant_id, outlet_id, amount, dt, merchant_name, outlet_name, scheme="VISA"):
    tx_uuid = str(uuid.uuid4())
    return {
        "transaction_id": tx_uuid,
        "transaction_no": f"TXN-{random.randint(100000, 999999)}",
        "outlet_id": outlet_id,
        "merchant_id": merchant_id,
        "profile_id": str(uuid.uuid4()),
        "transaction_timestamp": dt.isoformat(),
        "txn_date": dt.date().isoformat(),
        "txn_hour": str(dt.hour),
        "transaction_amount": round(amount, 2),
        "card_scheme": scheme,
        "merchant_name": merchant_name,
        "outlet_name": outlet_name
    }

def main():
    merchant_name = "Grandiose"
    outlet_name = "Grandiose - Al Zahiya"
    merchant_id = "4781c680-60c0-11f0-a6e9-033ce0bc078d"
    outlet_id = "bdbedf80-66fc-11f0-95ba-012c7c8027ee"

    now = datetime.now(timezone.utc)
    transactions = []

    # 1. Z-Score (AMOUNT_SPIKE)
    dt = now.replace(hour=14, minute=30, second=0)
    transactions.append(generate_tx(merchant_id, outlet_id, 95000.0, dt, merchant_name, outlet_name))

    # 2. Isolation Forest (PATTERN_BREAK)
    for i in range(5):
        dt = now.replace(hour=4, minute=random.randint(0, 59), second=0)
        transactions.append(generate_tx(merchant_id, outlet_id, random.uniform(5.0, 15.0), dt, merchant_name, outlet_name))

    # 3. Prophet (VOLUME_SPIKE)
    for i in range(100):
        dt = now.replace(hour=random.randint(9, 18), minute=random.randint(0, 59), second=0)
        transactions.append(generate_tx(merchant_id, outlet_id, random.uniform(10.0, 30.0), dt, merchant_name, outlet_name))

    # 4. Change Point (REGIME_CHANGE)
    for days_ago in range(17, 3, -1):
        base_dt = now - timedelta(days=days_ago)
        for i in range(15):
            dt = base_dt.replace(hour=random.randint(9, 18), minute=random.randint(0, 59), second=0)
            transactions.append(generate_tx(merchant_id, outlet_id, random.uniform(20.0, 50.0), dt, merchant_name, outlet_name))

    payload = {"transactions": transactions}

    with open("multi_algo_scenarios.json", "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(transactions)} transactions in multi_algo_scenarios.json")

if __name__ == "__main__":
    main()
