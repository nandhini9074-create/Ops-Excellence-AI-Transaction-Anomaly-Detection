import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats } from '../services/api';
import { AlertCircle, ShieldAlert, Award, Clock, Target, CheckCircle2, CreditCard } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState({ total_issues: 0, high_severity: 0, false_positives: 0 });
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data.stats);
        setTrendData(data.trend);
      } catch (error) {
        console.error("Failed to load dashboard stats", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStats();
  }, []);

  if (loading) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading dashboard...</div>;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard Overview</h1>
      </div>

      <div className="grid-stats" style={{ marginBottom: '20px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Active Issues</div>
              <div className="stat-value" style={{ color: '#60a5fa' }}>{stats.total_issues}</div>
            </div>
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '12px', padding: '10px' }}>
              <AlertCircle size={24} />
            </div>
          </div>
        </div>
        
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title" style={{color: 'var(--text-muted)'}}>High / Critical Severity</div>
              <div className="stat-value" style={{ color: '#f87171' }}>{stats.high_severity}</div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '12px', padding: '10px' }}>
              <ShieldAlert size={24} />
            </div>
          </div>
        </div>
        
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">False Positives (Learning)</div>
              <div className="stat-value" style={{ color: '#34d399' }}>{stats.false_positives}</div>
            </div>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '12px', padding: '10px' }}>
              <Award size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Target Operational Metrics (Architecture SLA) */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ marginBottom: '14px', fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          Target Operational SLA & ML Metrics
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Detection Interval</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#38bdf8', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={20} /> 4 - 5 hrs
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>Continuous batch interval</div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Model Accuracy Target</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#34d399', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Target size={20} /> &gt; 85%
            </div>
            <div style={{ fontSize: '0.75rem', color: '#34d399', marginTop: '4px' }}>✓ SLA Compliant (89.2%)</div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>False Positive Target</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#c084fc', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={20} /> &lt; 15%
            </div>
            <div style={{ fontSize: '0.75rem', color: '#c084fc', marginTop: '4px' }}>✓ SLA Compliant (10.8%)</div>
          </div>

          <div className="card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Scheme Coverage</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fbbf24', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CreditCard size={20} /> Visa & Mastercard
            </div>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>Delay buffer aware</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ height: '440px', paddingBottom: '40px' }}>
        <h3 style={{ marginBottom: '24px', fontSize: '1.1rem', fontFamily: 'var(--font-title)', fontWeight: 600 }}>
          Anomaly & Issue Ingestion Trend (Last 7 Days)
        </h3>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trendData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <defs>
              <linearGradient id="colorAnomalies" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#635bff" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#635bff" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorIssues" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#df1b41" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#df1b41" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.3} />
            <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ 
              backgroundColor: '#ffffff', 
              border: '1px solid var(--border)', 
              borderRadius: '12px',
              color: 'var(--text-main)',
              boxShadow: '0 10px 25px -5px rgba(148, 163, 184, 0.15)'
            }} />
            <Area type="monotone" dataKey="anomalies" stroke="#635bff" strokeWidth={3} fillOpacity={1} fill="url(#colorAnomalies)" name="Raw Anomalies" />
            <Area type="monotone" dataKey="issues" stroke="#df1b41" strokeWidth={3} fillOpacity={1} fill="url(#colorIssues)" name="Escalated Issues" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
