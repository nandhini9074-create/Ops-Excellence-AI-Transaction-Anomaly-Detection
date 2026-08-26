from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import json
from app.database.connection import get_db

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # 1. Total Active Issues
    total_issues = (await db.execute(text("SELECT COUNT(*) FROM issues WHERE status NOT IN ('RESOLVED', 'FALSE_POSITIVE', 'CLOSED', 'IGNORED')"))).scalar()
    
    # 2. High/Critical Severity Active Issues
    high_severity = (await db.execute(text("SELECT COUNT(*) FROM issues WHERE status NOT IN ('RESOLVED', 'FALSE_POSITIVE', 'CLOSED', 'IGNORED') AND severity IN ('HIGH', 'CRITICAL')"))).scalar()
    
    # 3. False Positives (all time)
    false_positives = (await db.execute(text("SELECT COALESCE(SUM(occurrence_count), 0) FROM issues WHERE status = 'FALSE_POSITIVE'"))).scalar()
    
    # 4. Real trend data from DB for the last 7 days
    query = text("""
        WITH anchor AS (
            SELECT COALESCE(MAX(date_trunc('day', created_at)), CURRENT_DATE) AS end_date FROM issues
        )
        SELECT 
            to_char(d.day, 'Dy') as name,
            COALESCE(SUM(i.occurrence_count), 0)::int as anomalies,
            COALESCE(SUM(i.occurrence_count) FILTER (WHERE i.status NOT IN ('FALSE_POSITIVE', 'IGNORED')), 0)::int as issues
        FROM 
            anchor,
            generate_series(
                anchor.end_date - INTERVAL '6 days', 
                anchor.end_date, 
                INTERVAL '1 day'
            ) AS d(day)
        LEFT JOIN issues i ON date_trunc('day', i.created_at) = d.day
        GROUP BY d.day
        ORDER BY d.day ASC;
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    trend_data = [dict(r) for r in rows]

    return {
        "stats": {
            "total_issues": total_issues or 0,
            "high_severity": high_severity or 0,
            "false_positives": false_positives or 0
        },
        "trend": trend_data
    }


@router.get("/baselines")
async def get_baselines(db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT 
            b.id,
            b.outlet_id,
            o.name as outlet_name,
            m.name as merchant_name,
            b.profile_data,
            b.analyzed_days,
            b.data_points_count,
            b.is_active,
            b.created_at
        FROM baselines b
        JOIN outlets o ON b.outlet_id = o.id
        JOIN merchants m ON o.merchant_id = m.id
        ORDER BY b.created_at DESC;
    """)
    result = await db.execute(query)
    rows = result.mappings().all()
    result_list = []
    for r in rows:
        d = dict(r)
        d['id'] = str(d['id'])
        d['outlet_id'] = str(d['outlet_id'])
        if isinstance(d.get('profile_data'), str):
            try:
                d['profile_data'] = json.loads(d['profile_data'])
            except Exception:
                pass
        if d.get('created_at'):
            d['created_at'] = d['created_at'].isoformat()
        result_list.append(d)
    return result_list
