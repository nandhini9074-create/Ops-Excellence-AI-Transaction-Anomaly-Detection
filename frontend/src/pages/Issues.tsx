import { useState, useEffect } from 'react';

// Mock data
const MOCK_ISSUES = [
  { id: '1', merchant_name: 'India Bistro', outlet_name: 'Dubai WTC', anomaly_type: 'VOLUME_SPIKE', severity: 'HIGH', status: 'OPEN', detected_at: '2026-08-14T10:00:00Z' },
  { id: '2', merchant_name: 'Coffee Planet', outlet_name: 'Etihad Plaza', anomaly_type: 'AMOUNT_DROP', severity: 'MEDIUM', status: 'INVESTIGATING', detected_at: '2026-08-14T09:15:00Z' },
  { id: '3', merchant_name: 'fnp.ae', outlet_name: 'E-Commerce', anomaly_type: 'PATTERN_BREAK', severity: 'CRITICAL', status: 'OPEN', detected_at: '2026-08-14T08:30:00Z' },
];

export default function Issues() {
  const [issues, setIssues] = useState(MOCK_ISSUES);

  const getBadgeClass = (severity: string) => {
    switch(severity) {
      case 'LOW': return 'badge badge-low';
      case 'MEDIUM': return 'badge badge-medium';
      case 'HIGH': return 'badge badge-high';
      case 'CRITICAL': return 'badge badge-critical';
      default: return 'badge';
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 className="page-title">Issue Management</h1>
        <button className="btn">Filter</button>
      </div>

      <div className="card table-container">
        <table>
          <thead>
            <tr>
              <th>Merchant</th>
              <th>Outlet</th>
              <th>Anomaly Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Detected</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {issues.map(issue => (
              <tr key={issue.id}>
                <td>{issue.merchant_name}</td>
                <td>{issue.outlet_name}</td>
                <td>{issue.anomaly_type}</td>
                <td><span className={getBadgeClass(issue.severity)}>{issue.severity}</span></td>
                <td><strong>{issue.status}</strong></td>
                <td>{new Date(issue.detected_at).toLocaleString()}</td>
                <td>
                  <button className="btn" style={{ padding: '4px 8px', fontSize: '0.8rem' }}>Review</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
