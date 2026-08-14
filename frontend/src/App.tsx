import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Activity, AlertTriangle, CheckSquare, LayoutDashboard, Settings } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Issues from './pages/Issues';

function App() {
  return (
    <Router>
      <div className="app-container">
        <aside className="sidebar">
          <div className="sidebar-title">Ops Excellence AI</div>
          <Link to="/" className="nav-link"><LayoutDashboard size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Dashboard</Link>
          <Link to="/issues" className="nav-link"><AlertTriangle size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Issues</Link>
          <Link to="/baselines" className="nav-link"><Activity size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Baselines</Link>
          <Link to="/feedback" className="nav-link"><CheckSquare size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Feedback</Link>
          <div style={{marginTop: 'auto'}}>
            <Link to="/settings" className="nav-link"><Settings size={18} style={{marginRight: '8px', verticalAlign: 'middle'}}/> Settings</Link>
          </div>
        </aside>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/issues" element={<Issues />} />
            {/* Stubs for other pages */}
            <Route path="/baselines" element={<div><h1 className="page-title">Baselines</h1><p>Under construction.</p></div>} />
            <Route path="/feedback" element={<div><h1 className="page-title">Feedback</h1><p>Under construction.</p></div>} />
            <Route path="/settings" element={<div><h1 className="page-title">Settings</h1><p>Under construction.</p></div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
