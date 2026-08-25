import pandas as pd
import numpy as np

def extract_volume_features(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    
    # Calculate daily volumes
    dates = pd.to_datetime(df['transaction_timestamp'])
    if isinstance(dates, pd.Timestamp):
        df['date'] = dates.date()
    elif hasattr(dates, 'dt'):
        df['date'] = dates.dt.date
    else:
        df['date'] = [d.date() if hasattr(d, 'date') else d for d in dates]
    daily_volumes = df.groupby('date').size()
    
    return {
        "total_transaction_count": len(df),
        "average_transactions_per_day": daily_volumes.mean(),
        "median_transactions_per_day": daily_volumes.median(),
        "std_transactions_per_day": daily_volumes.std() if len(daily_volumes) > 1 else 0.0,
        "min_daily_volume": daily_volumes.min(),
        "max_daily_volume": daily_volumes.max()
    }

def extract_amount_features(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    
    amounts = df['transaction_amount']
    
    return {
        "mean_amount": amounts.mean(),
        "median_amount": amounts.median(),
        "std_amount": amounts.std() if len(amounts) > 1 else 0.0,
        "p25_amount": float(np.percentile(amounts, 25)),
        "p50_amount": float(np.percentile(amounts, 50)),
        "p75_amount": float(np.percentile(amounts, 75)),
        "p90_amount": float(np.percentile(amounts, 90)),
        "p95_amount": float(np.percentile(amounts, 95)),
        "p99_amount": float(np.percentile(amounts, 99)),
        "min_amount": amounts.min(),
        "max_amount": amounts.max()
    }


