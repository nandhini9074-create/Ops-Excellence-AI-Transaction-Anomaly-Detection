import pandas as pd

def extract_time_and_seasonality_features(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
        
    df['datetime'] = pd.to_datetime(df['transaction_timestamp'])
    df['hour'] = df['datetime'].dt.hour  # type: ignore
    df['dayofweek'] = df['datetime'].dt.dayofweek  # type: ignore
    df['is_weekend'] = df['dayofweek'] >= 5
    
    # Active hours
    hourly_counts = df['hour'].value_counts()
    peak_hour = int(hourly_counts.idxmax())
    
    # Distribution
    hourly_dist = (hourly_counts / len(df)).to_dict()
    weekday_dist = (df[~df['is_weekend']].shape[0] / len(df)) if len(df) > 0 else 0
    weekend_dist = (df[df['is_weekend']].shape[0] / len(df)) if len(df) > 0 else 0
    
    # Group by hour to return dictionary
    hourly_dist_clean = {str(k): float(v) for k,v in hourly_dist.items()}
    
    # Weekly distribution
    weekly_counts = df['dayofweek'].value_counts()
    weekly_dist = (weekly_counts / len(df)).to_dict()
    weekly_percentage = {str(k): float(v) for k,v in weekly_dist.items()}
    
    return {
        "peak_transaction_hour": peak_hour,
        "hourly_distribution": hourly_dist_clean,
        "weekday_percentage": float(weekday_dist),
        "weekend_percentage": float(weekend_dist),
        "weekly_percentage": weekly_percentage
    }
