import { useState, useEffect } from 'react';
import { getIssues, acknowledgeIssue, resolveIssue } from '../services/api';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export default function Issues() {
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const data = await getIssues();
      setIssues(data);
    } catch (error) {
      console.error("Failed to load issues", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, []);

  const handleAcknowledge = async (id: string) => {
    try {
      await acknowledgeIssue(id);
      fetchIssues();
    } catch (error) {
      console.error("Failed to acknowledge issue", error);
    }
  };

  const handleResolve = async (id: string, isTrueAlert: boolean) => {
    const status = isTrueAlert ? 'RESOLVED' : 'FALSE_POSITIVE';
    const resolution = isTrueAlert ? 'Confirmed anomaly and escalated' : 'Marked as false positive after review';
    try {
      await resolveIssue(id, status, resolution);
      fetchIssues();
    } catch (error) {
      console.error("Failed to resolve issue", error);
    }
  };

  const getBadgeClass = (severity: string) => {
    switch(severity) {
      case 'LOW': return 'badge badge-low';
      case 'MEDIUM': return 'badge badge-medium';
      case 'HIGH': return 'badge badge-high';
      case 'CRITICAL': return 'badge badge-critical';
      default: return 'badge';
    }
  };

  const getTabCount = (filterKey: string) => {
    if (filterKey === 'ALL') return issues.length;
    return issues.filter(i => i.status === filterKey).length;
  };

  const renderRowActions = (issue: any) => {
    if (activeFilter === 'OPEN' && issue.status === 'OPEN') {
      return (
        <button 
          className="btn" 
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          onClick={() => handleAcknowledge(issue.id)}
        >
          Acknowledge
        </button>
      );
    }

    if (activeFilter === 'ACKNOWLEDGED' && issue.status === 'ACKNOWLEDGED') {
      return (
        <>
          <button 
            className="btn" 
            style={{ 
              padding: '6px 12px', 
              fontSize: '0.8rem',
              background: 'rgba(16, 185, 129, 0.1)', 
              color: '#34d399', 
              borderColor: 'rgba(16, 185, 129, 0.2)' 
            }}
            onClick={() => handleResolve(issue.id, true)}
          >
            True Alert
          </button>
          <button 
            className="btn" 
            style={{ 
              padding: '6px 12px', 
              fontSize: '0.8rem',
              background: 'rgba(239, 68, 68, 0.1)', 
              color: '#fca5a5', 
              borderColor: 'rgba(239, 68, 68, 0.2)' 
            }}
            onClick={() => handleResolve(issue.id, false)}
          >
            False Positive
          </button>
        </>
      );
    }

    if (issue.status === 'RESOLVED') {
      return (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <CheckCircle size={14} style={{ color: 'var(--success)' }} /> Confirmed Anomaly
        </span>
      );
    }

    if (issue.status === 'FALSE_POSITIVE') {
      return (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <XCircle size={14} style={{ color: 'var(--danger)' }} /> False Positive
        </span>
      );
    }

    return (
      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        {activeFilter === 'ALL' ? 'Overview Mode' : 'No Actions'}
      </span>
    );
  };

  const filteredIssues = issues.filter(issue => {
    if (activeFilter === 'ALL') return true;
    return issue.status === activeFilter;
  });

  if (loading && issues.length === 0) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading issues...</div>;
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Issue Management</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '6px' }}>
            Review, acknowledge, and resolve detected transaction anomalies.
          </p>
        </div>
        <button className="btn" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={fetchIssues}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', flexWrap: 'wrap' }}>
        {['ALL', 'OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_POSITIVE'].map(filter => {
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

      <div className="card table-container" style={{ padding: '0px', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Merchant & Outlet</th>
              <th>Anomaly Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Detected At</th>
              <th style={{ textAlign: 'right' }}>
                {activeFilter === 'OPEN' || activeFilter === 'ACKNOWLEDGED' ? 'Actions' : 'Details / Mode'}
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredIssues.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  No issues found matching this filter.
                </td>
              </tr>
            ) : filteredIssues.map(issue => (
              <tr key={issue.id}>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{issue.merchant_name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>{issue.outlet_name}</div>
                </td>
                <td style={{ verticalAlign: 'middle' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>{issue.anomaly_type}</span>
                  </div>
                </td>
                <td>
                  <span className={getBadgeClass(issue.severity)}>{issue.severity}</span>
                </td>
                <td>
                  <span style={{
                    color: issue.status === 'OPEN' ? '#f87171' : issue.status === 'ACKNOWLEDGED' ? '#fbbf24' : '#34d399',
                    fontWeight: 700,
                    fontSize: '0.85rem'
                  }}>
                    {issue.status}
                  </span>
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  {new Date(issue.detected_at).toLocaleString()}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                    {renderRowActions(issue)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
