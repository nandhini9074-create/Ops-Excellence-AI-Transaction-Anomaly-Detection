import React, { useState } from 'react';
import { ingestTransactions } from '../services/api';
import { Database, FileJson, CheckCircle, AlertTriangle, Type, FileSpreadsheet, UploadCloud } from 'lucide-react';
import * as XLSX from 'xlsx';

const DUMMY_TEMPLATE = {
  transactions: [
    {
      transaction_id: "txn-demo-001",
      transaction_no: "INV-2026-991",
      outlet_id: "bdbedf80-66fc-11f0-95ba-012c7c8027ee",
      merchant_id: "4781c680-60c0-11f0-a6e9-033ce0bc078d",
      profile_id: "profile-demo-001",
      transaction_timestamp: "2026-08-21T10:00:00Z",
      txn_date: "2026-08-21",
      txn_hour: "10",
      transaction_amount: 1250.50,
      card_scheme: "VISA",
      merchant_name: "Grandiose",
      outlet_name: "Grandiose - Marina"
    }
  ]
};

type TabMode = 'JSON' | 'FORM' | 'EXCEL';

export default function AddTransactions() {
  const [activeTab, setActiveTab] = useState<TabMode>('JSON');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{success?: boolean, message?: string, details?: string} | null>(null);

  // JSON State
  const [jsonInput, setJsonInput] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    transaction_id: '',
    outlet_id: '',
    merchant_id: '',
    transaction_timestamp: new Date().toISOString().slice(0, 16), // YYYY-MM-DDThh:mm
    transaction_amount: ''
  });

  // Excel State
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [excelDataPreview, setExcelDataPreview] = useState<any[] | null>(null);

  const loadTemplate = () => {
    setJsonInput(JSON.stringify(DUMMY_TEMPLATE, null, 2));
    setResult(null);
  };

  const handleJsonSubmit = async () => {
    try {
      if (!jsonInput.trim()) throw new Error("Input is empty.");
      
      let parsedData;
      try {
        parsedData = JSON.parse(jsonInput);
      } catch (err) {
        throw new Error("Invalid JSON format. Please check your syntax.");
      }

      if (!parsedData.transactions || !Array.isArray(parsedData.transactions)) {
        throw new Error("JSON must contain a 'transactions' array at the root.");
      }
      return parsedData.transactions;
    } catch (e: any) {
      throw e;
    }
  };

  const handleFormSubmit = async () => {
    if (!formData.outlet_id || !formData.merchant_id || !formData.transaction_timestamp || !formData.transaction_amount) {
      throw new Error("Please fill in all required fields.");
    }
    
    const ts = new Date(formData.transaction_timestamp);
    const txn_date = ts.toISOString().split('T')[0];
    const txn_hour = ts.getUTCHours().toString();

    return [{
      transaction_id: formData.transaction_id || `txn-manual-${Date.now()}`,
      outlet_id: formData.outlet_id,
      merchant_id: formData.merchant_id,
      transaction_timestamp: ts.toISOString(),
      txn_date,
      txn_hour,
      transaction_amount: parseFloat(formData.transaction_amount)
    }];
  };

  const handleExcelUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setExcelFile(file);
    setResult(null);

    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const bstr = evt.target?.result;
        const wb = XLSX.read(bstr, { type: 'binary' });
        const wsname = wb.SheetNames[0];
        const ws = wb.Sheets[wsname];
        const data = XLSX.utils.sheet_to_json(ws);
        setExcelDataPreview(data);
      } catch (err) {
        setResult({ success: false, message: "Failed to parse Excel file", details: "Ensure it is a valid .xlsx or .csv file." });
      }
    };
    reader.readAsBinaryString(file);
  };

  const handleExcelSubmit = async () => {
    if (!excelDataPreview || excelDataPreview.length === 0) {
      throw new Error("No valid data found in the uploaded file.");
    }

    // Attempt to map Excel rows to Transaction objects
    const mappedTransactions = excelDataPreview.map((row, idx) => {
      // Very basic mapping, expecting columns to match schema fields
      if (!row.outlet_id || !row.merchant_id || !row.transaction_amount) {
        throw new Error(`Row ${idx + 1} is missing required fields (outlet_id, merchant_id, transaction_amount)`);
      }

      // Try to parse timestamp, or fallback to current time
      const tsStr = row.transaction_timestamp ? String(row.transaction_timestamp) : new Date().toISOString();
      const ts = new Date(tsStr);
      if (isNaN(ts.getTime())) throw new Error(`Row ${idx + 1} has invalid transaction_timestamp`);

      return {
        ...row,
        transaction_id: row.transaction_id ? String(row.transaction_id) : `txn-xl-${Date.now()}-${idx}`,
        outlet_id: String(row.outlet_id),
        merchant_id: String(row.merchant_id),
        transaction_timestamp: ts.toISOString(),
        txn_date: row.txn_date || ts.toISOString().split('T')[0],
        txn_hour: row.txn_hour || ts.getUTCHours().toString(),
        transaction_amount: parseFloat(row.transaction_amount)
      };
    });

    return mappedTransactions;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    try {
      let transactionsToIngest = [];

      if (activeTab === 'JSON') {
        transactionsToIngest = await handleJsonSubmit();
      } else if (activeTab === 'FORM') {
        transactionsToIngest = await handleFormSubmit();
      } else if (activeTab === 'EXCEL') {
        transactionsToIngest = await handleExcelSubmit();
      }

      const response = await ingestTransactions(transactionsToIngest);
      setResult({
        success: true,
        message: response.message || `Successfully ingested ${transactionsToIngest.length} transactions!`
      });
      
      if (activeTab === 'JSON') setJsonInput('');
      if (activeTab === 'EXCEL') { setExcelFile(null); setExcelDataPreview(null); }
    } catch (error: any) {
      setResult({
        success: false,
        message: error.message || "An error occurred",
        details: error.response?.data?.detail || "Make sure all required fields are present."
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Ingest Transactions</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '6px' }}>
            Manually add new transactions for monitoring and baseline analysis.
          </p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: '800px', margin: '0 auto', padding: 0, overflow: 'hidden' }}>
        
        {/* Tabs */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.02)' }}>
          <button 
            onClick={() => { setActiveTab('JSON'); setResult(null); }}
            style={{
              flex: 1, padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', cursor: 'pointer',
              background: activeTab === 'JSON' ? 'transparent' : 'rgba(0,0,0,0.2)',
              border: 'none', borderBottom: activeTab === 'JSON' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'JSON' ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: 600, fontSize: '0.95rem'
            }}
          >
            <FileJson size={18} /> JSON Payload
          </button>
          <button 
            onClick={() => { setActiveTab('FORM'); setResult(null); }}
            style={{
              flex: 1, padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', cursor: 'pointer',
              background: activeTab === 'FORM' ? 'transparent' : 'rgba(0,0,0,0.2)',
              border: 'none', borderBottom: activeTab === 'FORM' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'FORM' ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: 600, fontSize: '0.95rem'
            }}
          >
            <Type size={18} /> Manual Form
          </button>
          <button 
            onClick={() => { setActiveTab('EXCEL'); setResult(null); }}
            style={{
              flex: 1, padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', cursor: 'pointer',
              background: activeTab === 'EXCEL' ? 'transparent' : 'rgba(0,0,0,0.2)',
              border: 'none', borderBottom: activeTab === 'EXCEL' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'EXCEL' ? 'var(--primary)' : 'var(--text-muted)',
              fontWeight: 600, fontSize: '0.95rem'
            }}
          >
            <FileSpreadsheet size={18} /> Excel Upload
          </button>
        </div>

        <div style={{ padding: '24px' }}>
          
          {/* JSON CONTENT */}
          {activeTab === 'JSON' && (
            <>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Paste a JSON object containing a <code style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>transactions</code> array.
              </p>
              <textarea 
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                placeholder='{"transactions": [ ... ]}'
                style={{
                  width: '100%', height: '300px', backgroundColor: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)',
                  borderRadius: '8px', padding: '16px', color: 'var(--text-primary)', fontFamily: 'monospace',
                  fontSize: '0.9rem', resize: 'vertical', marginBottom: '16px'
                }}
                spellCheck={false}
              />
            </>
          )}

          {/* FORM CONTENT */}
          {activeTab === 'FORM' && (
            <div style={{ display: 'grid', gap: '16px', marginBottom: '16px' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Manually enter a single transaction. Missing optional fields will be auto-generated.
              </p>
              
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>Outlet ID *</label>
                <input type="text" className="input" value={formData.outlet_id} onChange={(e) => setFormData({...formData, outlet_id: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} placeholder="e.g. bdbedf80-..." />
              </div>
              
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>Merchant ID *</label>
                <input type="text" className="input" value={formData.merchant_id} onChange={(e) => setFormData({...formData, merchant_id: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} placeholder="e.g. 4781c680-..." />
              </div>

              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>Transaction Amount *</label>
                  <input type="number" step="0.01" value={formData.transaction_amount} onChange={(e) => setFormData({...formData, transaction_amount: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} placeholder="0.00" />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>Timestamp *</label>
                  <input type="datetime-local" value={formData.transaction_timestamp} onChange={(e) => setFormData({...formData, transaction_timestamp: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>Transaction ID (Optional)</label>
                <input type="text" className="input" value={formData.transaction_id} onChange={(e) => setFormData({...formData, transaction_id: e.target.value})} style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)', background: 'rgba(0,0,0,0.2)', color: 'white' }} placeholder="Auto-generated if left blank" />
              </div>
            </div>
          )}

          {/* EXCEL CONTENT */}
          {activeTab === 'EXCEL' && (
            <div style={{ marginBottom: '16px' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Upload a `.xlsx` or `.csv` file. The first row must contain column headers matching the schema fields (e.g. `outlet_id`, `merchant_id`, `transaction_amount`).
              </p>
              
              <label style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                height: '200px', border: '2px dashed var(--border)', borderRadius: '8px', cursor: 'pointer',
                background: 'rgba(0,0,0,0.2)', transition: 'all 0.2s'
              }}
              onDragOver={(e) => e.preventDefault()}
              >
                <UploadCloud size={48} style={{ color: 'var(--primary)', marginBottom: '16px' }} />
                <div style={{ fontWeight: 600, marginBottom: '8px' }}>Click to Browse or Drag File Here</div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{excelFile ? excelFile.name : 'Supports .xlsx, .csv'}</div>
                <input type="file" accept=".xlsx, .csv" onChange={handleExcelUpload} style={{ display: 'none' }} />
              </label>

              {excelDataPreview && (
                <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '8px' }}>Parsed {excelDataPreview.length} rows</div>
                  <pre style={{ fontSize: '0.75rem', color: 'var(--text-muted)', overflowX: 'auto' }}>
                    {JSON.stringify(excelDataPreview.slice(0, 2), null, 2)}
                    {excelDataPreview.length > 2 && '\n...'}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* SHARED RESULT ALERT */}
          {result && (
            <div style={{ 
              padding: '12px 16px', borderRadius: '8px', marginBottom: '16px',
              backgroundColor: result.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${result.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
              display: 'flex', alignItems: 'flex-start', gap: '12px'
            }}>
              {result.success ? (
                <CheckCircle size={20} style={{ color: '#34d399', flexShrink: 0 }} />
              ) : (
                <AlertTriangle size={20} style={{ color: '#fca5a5', flexShrink: 0 }} />
              )}
              <div>
                <div style={{ fontWeight: 600, color: result.success ? '#34d399' : '#fca5a5', fontSize: '0.95rem' }}>
                  {result.message}
                </div>
                {result.details && (
                  <div style={{ fontSize: '0.85rem', color: result.success ? '#a7f3d0' : '#fecaca', marginTop: '4px' }}>
                    {result.details}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SHARED ACTIONS */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            {activeTab === 'JSON' ? (
              <button className="btn" onClick={loadTemplate} style={{ opacity: 0.8 }}>
                Load Template
              </button>
            ) : <div/>}
            <button 
              className="btn btn-primary" 
              onClick={handleSubmit} 
              disabled={loading}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: '150px', justifyContent: 'center' }}
            >
              {loading ? 'Processing...' : (
                <>
                  <Database size={16} /> Ingest Transactions
                </>
              )}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
