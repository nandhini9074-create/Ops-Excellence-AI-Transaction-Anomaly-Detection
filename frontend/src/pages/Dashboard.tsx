import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock data for initial render without backend
const mockData = [
  { name: 'Mon', anomalies: 4, issues: 2 },
  { name: 'Tue', anomalies: 3, issues: 1 },
  { name: 'Wed', anomalies: 7, issues: 5 },
  { name: 'Thu', anomalies: 2, issues: 2 },
  { name: 'Fri', anomalies: 6, issues: 4 },
  { name: 'Sat', anomalies: 1, issues: 0 },
  { name: 'Sun', anomalies: 2, issues: 1 },
];

export default function Dashboard() {
  const [stats, setStats] = useState({ total_issues: 0, high_severity: 0, false_positives: 0 });

  useEffect(() => {
    // In a real app, fetch from /api/v1/analytics
    setStats({
      total_issues: 24,
      high_severity: 5,
      false_positives: 3
    });
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
      </div>

      <div className="grid-stats">
        <div className="card">
          <div className="stat-title">Active Issues</div>
          <div className="stat-value">{stats.total_issues}</div>
        </div>
        <div className="card">
          <div className="stat-title" style={{color: 'var(--danger)'}}>High/Critical Severity</div>
          <div className="stat-value">{stats.high_severity}</div>
        </div>
        <div className="card">
          <div className="stat-title" style={{color: 'var(--success)'}}>False Positives (Learning)</div>
          <div className="stat-value">{stats.false_positives}</div>
        </div>
      </div>

      <div className="card" style={{ height: '400px' }}>
        <h3 style={{ marginBottom: '24px' }}>Anomaly Trend (Last 7 Days)</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={mockData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
            <Line type="monotone" dataKey="anomalies" stroke="#3b82f6" strokeWidth={3} />
            <Line type="monotone" dataKey="issues" stroke="#ef4444" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
