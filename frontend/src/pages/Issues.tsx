import { useState, useEffect } from 'react';
import { getIssues, acknowledgeIssue, resolveIssue, markInProgress } from '../services/api';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export default function Issues() {
  const [issues, setIssues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [feedbackInputs, setFeedbackInputs] = useState<Record<string, string>>({});
  const [activeResolution, setActiveResolution] = useState<Record<string, 'RESOLVED' | 'FALSE_POSITIVE' | 'IGNORED' | null>>({});

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

  const handleInProgress = async (id: string) => {
    try {
      await markInProgress(id);
      fetchIssues();
    } catch (error) {
      console.error("Failed to mark in progress", error);
    }
  };

  const handleResolve = async (id: string, resolutionType: 'RESOLVED' | 'FALSE_POSITIVE' | 'IGNORED') => {
    const status = resolutionType;
    const customFeedback = feedbackInputs[id]?.trim();
    let resolution = '';
    if (resolutionType === 'RESOLVED') resolution = 'Confirmed anomaly and escalated';
    else if (resolutionType === 'FALSE_POSITIVE') resolution = 'Marked as false positive after review';
    else if (resolutionType === 'IGNORED') resolution = 'Ignored by operator';
    
    try {
      await resolveIssue(id, status, resolution, customFeedback);
      setFeedbackInputs(prev => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      fetchIssues();
    } catch (error) {
      console.error("Failed to resolve issue", error);
    }
  };

  const getBadgeClass = (severity: string) => {
    switch (severity) {
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
    if (activeFilter === 'ALL') {
      return (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          {issue.status.replace('_', ' ')}
        </span>
      );
    }

    if (['NEW', 'ACKNOWLEDGED', 'IN_PROGRESS'].includes(issue.status)) {
      const resolvingState = activeResolution[issue.id];

      if (resolvingState) {
        const isResolve = resolvingState === 'RESOLVED';
        const isIgnored = resolvingState === 'IGNORED';
        const placeholderText = isResolve ? 'Resolution' : isIgnored ? 'Ignore Reason' : 'False Positive';
        
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: '220px' }}>
            <input
              type="text"
              placeholder={`Feedback for ${placeholderText}...`}
              value={feedbackInputs[issue.id] || ''}
              onChange={(e) => setFeedbackInputs({ ...feedbackInputs, [issue.id]: e.target.value })}
              style={{
                width: '100%', padding: '6px', borderRadius: '4px',
                border: '1px solid var(--border)', background: 'rgba(255,255,255,0.9)', color: '#3d0377ff', fontSize: '0.8rem', outline: 'none'
              }}
            />
            <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
              <button
                className="btn"
                style={{ padding: '4px 8px', fontSize: '0.75rem', opacity: 0.8 }}
                onClick={() => setActiveResolution({ ...activeResolution, [issue.id]: null })}
              >
                Cancel
              </button>
              <button
                className="btn"
                style={{ padding: '4px 8px', fontSize: '0.75rem', background: isResolve ? 'var(--primary)' : '#ef4444', color: 'white', border: 'none' }}
                onClick={() => {
                  handleResolve(issue.id, resolvingState);
                  setActiveResolution({ ...activeResolution, [issue.id]: null });
                }}
              >
                OK
              </button>
            </div>
          </div>
        );
      }

      return (
        <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
          {issue.status === 'NEW' && (
            <button
              className="btn"
              style={{ padding: '6px 10px', fontSize: '0.8rem' }}
              onClick={() => handleAcknowledge(issue.id)}
            >
              Acknowledge
            </button>
          )}
          {/*
          {issue.status === 'ACKNOWLEDGED' && (
            <button
              className="btn"
              style={{ padding: '6px 10px', fontSize: '0.8rem', background: 'var(--accent)', color: 'white' }}
              onClick={() => handleInProgress(issue.id)}
            >
              Investigate
            </button>
          )}
          */}
          {(issue.status === 'ACKNOWLEDGED' || issue.status === 'IN_PROGRESS') && (
            <>
              <button
                className="btn btn-primary"
                style={{ padding: '6px 10px', fontSize: '0.8rem' }}
                onClick={() => setActiveResolution({ ...activeResolution, [issue.id]: 'RESOLVED' })}
              >
                Resolve
              </button>
              <button
                className="btn"
                style={{ padding: '6px 10px', fontSize: '0.8rem', color: '#f8eff9ff', borderColor: 'rgba(252,165,165,0.3)' }}
                onClick={() => setActiveResolution({ ...activeResolution, [issue.id]: 'FALSE_POSITIVE' })}
              >
                False Positive
              </button>
              <button
                className="btn"
                style={{ padding: '6px 10px', fontSize: '0.8rem', color: '#a1a1aa', borderColor: 'rgba(161,161,170,0.3)' }}
                onClick={() => setActiveResolution({ ...activeResolution, [issue.id]: 'IGNORED' })}
              >
                Ignore
              </button>
            </>
          )}
        </div>
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
    
    if (issue.status === 'IGNORED') {
      return (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <XCircle size={14} style={{ color: 'var(--text-muted)' }} /> Ignored
        </span>
      );
    }

    return null;
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
        {/* 'IN_PROGRESS' commented out for later use */}
        {['ALL', 'NEW', 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_POSITIVE', 'IGNORED'].map(filter => {
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
              <th>Scheme</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Detected At</th>
              <th style={{ textAlign: 'right' }}>Actions / Status</th>
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
                    {issue.occurrence_count > 1 && (
                      <span style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 600 }}>
                        ×{issue.occurrence_count}
                      </span>
                    )}
                  </div>
                  {issue.remarks && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={issue.remarks}>
                      {issue.remarks}
                    </div>
                  )}
                </td>
                <td>
                  {issue.scheme ? (
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{issue.scheme}</span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>-</span>
                  )}
                </td>
                <td>
                  <span className={getBadgeClass(issue.severity)}>{issue.severity}</span>
                </td>
                <td>
                  <span style={{
                    color: (issue.status === 'NEW') ? '#f87171' : (issue.status === 'ACKNOWLEDGED' || issue.status === 'IN_PROGRESS') ? '#2427fbff' : '#34d399',
                    fontWeight: 700,
                    fontSize: '0.85rem'
                  }}>
                    {issue.status}
                  </span>
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  {new Date(issue.last_detected_at || issue.created_at).toLocaleString()}
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
