import { useState, useEffect } from 'react';
import { getBaselines } from '../services/api';
import { Activity, RefreshCw, Search, Layers, Clock, Database } from 'lucide-react';

export default function Baselines() {
  const [baselines, setBaselines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchBaselines = async () => {
    setLoading(true);
    try {
      const data = await getBaselines();
      setBaselines(data);
    } catch (error) {
      console.error("Failed to fetch baselines", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBaselines();
  }, []);

  const filteredBaselines = baselines.filter(b => 
    b.merchant_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.outlet_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activeCount = baselines.filter(b => b.is_active === 'true' || b.is_active === true).length;
  const totalSamples = baselines.reduce((acc, b) => acc + (b.data_points_count || 0), 0);

  if (loading && baselines.length === 0) {
    return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading baseline profiles...</div>;
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Baseline Profiles</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '6px' }}>
            Historical 30-day statistical thresholds computed per merchant outlet.
          </p>
        </div>
        <button className="btn" style={{ display: 'flex', alignItems: 'center', gap: '8px' }} onClick={fetchBaselines}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid-stats" style={{ marginBottom: '24px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Active Profiles</div>
              <div className="stat-value" style={{ color: '#60a5fa' }}>{activeCount}</div>
            </div>
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', borderRadius: '12px', padding: '10px' }}>
              <Activity size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Avg History Window</div>
              <div className="stat-value" style={{ color: '#34d399' }}>30 Days</div>
            </div>
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', borderRadius: '12px', padding: '10px' }}>
              <Clock size={24} />
            </div>
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-title">Evaluated Data Points</div>
              <div className="stat-value" style={{ color: '#c084fc' }}>{totalSamples.toLocaleString()}</div>
            </div>
            <div style={{ background: 'rgba(192, 132, 252, 0.1)', color: '#c084fc', borderRadius: '12px', padding: '10px' }}>
              <Database size={24} />
            </div>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: '8px', padding: '8px 16px', maxWidth: '400px' }}>
        <Search size={18} style={{ color: 'var(--text-muted)', marginRight: '10px' }} />
        <input 
          type="text" 
          placeholder="Filter by merchant or outlet name..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ background: 'transparent', border: 'none', color: '#f8fafc', outline: 'none', width: '100%', fontSize: '0.9rem' }}
        />
      </div>

      {/* Data Table */}
      <div className="card table-container" style={{ padding: '0px', overflow: 'hidden' }}>
        <table>
          <thead>
            <tr>
              <th>Merchant & Outlet</th>
              <th>Analyzed Window</th>
              <th>Sample Count</th>
              <th>Mean Txn Amount</th>
              <th>Peak Txn Hour</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Created At</th>
            </tr>
          </thead>
          <tbody>
            {filteredBaselines.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  No baseline profiles found.
                </td>
              </tr>
            ) : filteredBaselines.map(b => {
              const meanAmount = b.profile_data?.mean_amount ? `\$${Number(b.profile_data.mean_amount).toFixed(2)}` : 'N/A';
              const peakHour = b.profile_data?.peak_transaction_hour !== undefined ? `${b.profile_data.peak_transaction_hour}:00` : 'N/A';

              return (
                <tr key={b.id}>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{b.merchant_name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>{b.outlet_name}</div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{b.analyzed_days} Days</span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>{b.data_points_count?.toLocaleString()} samples</span>
                  </td>
                  <td>
                    <span style={{ fontWeight: 700, color: '#38bdf8' }}>{meanAmount}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: '#fbbf24', fontWeight: 600 }}>{peakHour}</span>
                  </td>
                  <td>
                    <span style={{
                      color: b.is_active === 'true' || b.is_active === true ? '#34d399' : '#f87171',
                      fontWeight: 700,
                      fontSize: '0.85rem',
                      background: b.is_active === 'true' || b.is_active === true ? 'rgba(52, 211, 153, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                      padding: '4px 10px',
                      borderRadius: '12px'
                    }}>
                      {b.is_active === 'true' || b.is_active === true ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                    {new Date(b.created_at).toLocaleString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
