import { useState, useEffect } from 'react';
import { getFeedbackLogs } from '../services/api';
import { RefreshCw, CheckCircle, XCircle, Search, MessageSquare, ShieldCheck, AlertOctagon } from 'lucide-react';

export default function Feedback() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchFeedback = async () => {
    setLoading(true);
    try {
      const data = await getFeedbackLogs();
      setLogs(data);
    } catch (error) {
      console.error("Failed to load feedback logs", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeedback();
  }, []);

  const filteredLogs = logs.filter(log => {
    const matchesFilter = activeFilter === 'ALL' || log.feedback_type === activeFilter;
    const matchesSearch = (
      log.anomaly_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.merchant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.outlet_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.comments?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    return matchesFilter && matchesSearch;
  });

  const trueAlertsCount = logs.filter(l => l.feedback_type === 'TRUE_ALERT' || l.feedback_type === 'RESOLVED').length;
  const falsePositivesCount = logs.filter(l => l.feedback_type === 'FALSE_POSITIVE').length;
  const uncertainCount = logs.filter(l => l.feedback_type === 'UNCERTAIN').length;

  const getTabCount = (type: string) => {
    if (type === 'ALL') return logs.length;
    if (type === 'TRUE_ALERT') return trueAlertsCount;
    if (type === 'FALSE_POSITIVE') return falsePositivesCount;
    if (type === 'UNCERTAIN') return uncertainCount;
    return 0;
  };

  if (loading && logs.length === 0) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading human feedback audit logs...</div>;
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Human Feedback Audit Logs</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '6px' }}>
            Operator feedback history used for human-in-the-loop ML model retuning and threshold calibration.
          </p>
        </div>
        <button className="btn" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={fetchFeedback}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid-stats" style={{ marginBottom: '24px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Total Feedback Logged</div>
              <div className="stat-value" style={{ color: '#60a5fa' }}>{logs.length}</div>
            </div>
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '12px', padding: '10px' }}>
              <MessageSquare size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Confirmed True Alerts</div>
              <div className="stat-value" style={{ color: '#34d399' }}>{trueAlertsCount}</div>
            </div>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '12px', padding: '10px' }}>
              <ShieldCheck size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Flagged False Positives</div>
              <div className="stat-value" style={{ color: '#f87171' }}>{falsePositivesCount}</div>
            </div>
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '12px', padding: '10px' }}>
              <AlertOctagon size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'TRUE_ALERT', 'FALSE_POSITIVE', 'UNCERTAIN'].map(filter => {
            const count = getTabCount(filter);
            return (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                style={{
                  background: activeFilter === filter ? 'var(--primary-glow)' : 'transparent',
                  color: activeFilter === filter ? '#60a5fa' : 'var(--text-muted)',
                  border: activeFilter === filter ? '1px solid rgba(59, 130, 246, 0.2)' : '1px solid transparent',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span>{filter.replace('_', ' ')}</span>
                <span style={{
                  background: activeFilter === filter ? 'rgba(96, 165, 250, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  fontWeight: 700
                }}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '8px', padding: '8px 16px', width: '320px' }}>
          <Search size={18} style={{ color: 'var(--text-muted)', marginRight: '10px' }} />
          <input 
            type="text" 
            placeholder="Search feedback notes..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: '#f8fafc', outline: 'none', width: '100%', fontSize: '0.9rem' }}
          />
        </div>
      </div>

      {/* Data Table */}
      <div className="card table-container" style={{ padding: '0px', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Anomaly & Issue ID</th>
              <th>Merchant & Outlet</th>
              <th>Classification</th>
              <th>Operator Resolution / Comments</th>
              <th>Submitted By</th>
              <th style={{ textAlign: 'right' }}>Logged At</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  No feedback records found.
                </td>
              </tr>
            ) : filteredLogs.map(log => (
              <tr key={log.id}>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{log.anomaly_type || 'Anomaly Ticket'}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: '2px' }}>
                    ID: {log.issue_id ? log.issue_id.substring(0, 8) : 'N/A'}...
                  </div>
                </td>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{log.merchant_name || 'System Merchant'}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>{log.outlet_name || 'Main Outlet'}</div>
                </td>
                <td>
                  <span style={{
                    color: log.feedback_type === 'TRUE_ALERT' || log.feedback_type === 'RESOLVED' ? '#34d399' : log.feedback_type === 'UNCERTAIN' ? '#fbbf24' : '#f87171',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: log.feedback_type === 'TRUE_ALERT' || log.feedback_type === 'RESOLVED' ? 'rgba(52, 211, 153, 0.1)' : log.feedback_type === 'UNCERTAIN' ? 'rgba(251, 191, 36, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                    padding: '4px 10px',
                    borderRadius: '12px'
                  }}>
                    {log.feedback_type === 'TRUE_ALERT' || log.feedback_type === 'RESOLVED' ? (
                      <><CheckCircle size={14} /> TRUE ALERT</>
                    ) : log.feedback_type === 'UNCERTAIN' ? (
                      <><AlertOctagon size={14} style={{ color: '#fbbf24' }} /> UNCERTAIN</>
                    ) : (
                      <><XCircle size={14} /> FALSE POSITIVE</>
                    )}
                  </span>
                </td>
                <td>
                  <div style={{ fontSize: '0.85rem', color: '#e2e8f0', fontWeight: 500 }}>
                    {log.root_cause || log.comments || 'Feedback submitted by operator during issue triage.'}
                  </div>
                </td>
                <td>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                    {log.submitted_by || 'Operations Analyst'}
                  </span>
                </td>
                <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  {new Date(log.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
