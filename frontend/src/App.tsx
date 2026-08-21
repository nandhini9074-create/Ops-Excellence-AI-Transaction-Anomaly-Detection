import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Activity, AlertTriangle, CheckSquare, LayoutDashboard, Settings, User, Database } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Issues from './pages/Issues';
import Baselines from './pages/Baselines';
import Feedback from './pages/Feedback';
import AddTransactions from './pages/AddTransactions';

// Inner component to access router context for active navigation styling
function SidebarNav() {
  return (
    <aside className="sidebar">
      <div>
        <div className="sidebar-title">Ops Excellence AI</div>
        <div className="sidebar-status">
          <span className="status-pulse"></span>
          Live Monitoring Active
        </div>
      </div>
      
      <NavLink to="/" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><LayoutDashboard size={18}/> Dashboard</NavLink>
      <NavLink to="/issues" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><AlertTriangle size={18}/> Issues</NavLink>
      <NavLink to="/baselines" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><Activity size={18}/> Baselines</NavLink>
      <NavLink to="/feedback" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><CheckSquare size={18}/> Feedback</NavLink>
      <NavLink to="/add-transactions" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}><Database size={18}/> Add Transactions</NavLink>
      
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '16px 18px',
          borderTop: '1px solid var(--border)',
          marginTop: '8px'
        }}>
          <div style={{
            background: 'var(--primary-glow)',
            color: '#60a5fa',
            borderRadius: '50%',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <User size={16} />
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Operations Team</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Administrator</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <SidebarNav />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/issues" element={<Issues />} />
            <Route path="/baselines" element={<Baselines />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/add-transactions" element={<AddTransactions />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
