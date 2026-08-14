import json
import os
import sys

# Add parent dir to path to import data_pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.generators.dataset_generator import generate_transactions

def main():
    print("Generating 2,000 transactions (1,500 normal, 500 group)...")
    transactions = generate_transactions(1500, 500, 90)
    
    out_file = "transactions.json"
    with open(out_file, "w") as f:
        json.dump(transactions, f, indent=2)
        
    print(f"Successfully generated {len(transactions)} transactions to {out_file}")

if __name__ == "__main__":
    main()
