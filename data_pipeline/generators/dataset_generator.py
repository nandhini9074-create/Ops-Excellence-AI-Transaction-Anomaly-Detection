import json
import uuid
import random
from datetime import datetime, timedelta

KNOWN_GROUP_ID = "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e"

# We define some outlets from the prompt
MERCHANTS_OUTLETS = [
    {
        "merchant_id": "243ceb70-58c1-11f0-bf5d-035ea8dfea80",
        "merchant_name": "India Bistro",
        "outlets": [
            {
                "outlet_id": "3614a880-5be4-11f0-8012-c54b1b5cd9d0",
                "outlet_name": "India Bistro - Dubai World Trade Center",
                "profile_id": "a154a1d8-c6f5-47af-a14d-11052271c3e7",
                "type": "restaurant",
                "frequency": "medium",
                "amount_range": (30, 250)
            }
        ]
    },
    {
        "merchant_id": "137e3560-5c76-11f0-8241-fbb6908a2b21",
        "merchant_name": "fnp.ae",
        "outlets": [
            {
                "outlet_id": "035af650-5c99-11f0-ac66-798b2b114fd3",
                "outlet_name": "fnp.ae - E-Commerce",
                "profile_id": str(uuid.uuid4()), # Generate a profile_id if not given
                "type": "ecommerce",
                "frequency": "high",
                "amount_range": (50, 400)
            }
        ]
    },
    {
        "merchant_id": "b09e62e0-0eba-11ee-adc6-1f788b745ca1",
        "merchant_name": "Coffee Planet",
        "outlets": [
            {
                "outlet_id": "e8ae6be0-9b62-11ef-9222-89af7ea4ecaf",
                "outlet_name": "Coffee Planet - Etihad Plaza",
                "profile_id": str(uuid.uuid4()),
                "type": "coffee",
                "frequency": "high",
                "amount_range": (15, 60)
            }
        ]
    }
]

def generate_transactions(num_normal=1500, num_group=500, days_history=90):
    transactions = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_history)
    
    total = num_normal + num_group
    
    for i in range(total):
        is_group = i >= num_normal
        
        # Pick random merchant and outlet based on their frequency (simplified)
        merchant = random.choice(MERCHANTS_OUTLETS)
        outlet = random.choice(merchant["outlets"])
        
        # Determine amount based on outlet type
        min_amt, max_amt = outlet["amount_range"]
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        # Add some occasional injected anomalies for testing (1% chance)
        if random.random() < 0.01:
            amount = round(amount * random.uniform(5, 10), 2)
            
        # Random timestamp
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        tx_time = start_date + timedelta(seconds=random_seconds)
        
        tx = {
            "outlet_id": outlet["outlet_id"],
            "merchant_id": merchant["merchant_id"],
            "profile_id": outlet["profile_id"],
            "transaction_timestamp": tx_time.isoformat(),
            "posting_timestamp": (tx_time + timedelta(hours=1)).isoformat(),
            "txn_date": tx_time.strftime("%Y-%m-%d"),
            "txn_hour": tx_time.strftime("%H"),
            "transaction_amount": amount,
            "card_scheme": random.choice(["VISA", "MASTERCARD"]),
            "merchant_name": merchant["merchant_name"],
            "outlet_name": outlet["outlet_name"],
            "outlet_status": "ACTIVE"
        }
        
        if is_group:
            tx["group_id"] = KNOWN_GROUP_ID
            tx["group_transaction_id"] = str(uuid.uuid4())
            tx["transaction_id"] = None
            tx["transaction_no"] = None
        else:
            tx["group_id"] = None
            tx["group_transaction_id"] = None
            tx["transaction_id"] = str(uuid.uuid4())
            tx["transaction_no"] = f"TXN-{random.randint(100000, 999999)}"
            
        transactions.append(tx)
        
    # Sort by timestamp
    transactions.sort(key=lambda x: x["transaction_timestamp"])
    
    return transactions

def load_dataset(file_path: str):
    import pandas as pd
    import json
    import os
    
    # Try resolving relative path if not found directly
    if not os.path.exists(file_path):
        # Check if the file is in parent directories
        alt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
            
    if file_path.endswith('.json'):
        return pd.read_json(file_path)
    elif file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    else:
        try:
            return pd.read_json(file_path)
        except Exception:
            return pd.read_csv(file_path)
