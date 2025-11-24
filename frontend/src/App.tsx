import React, { useState } from 'react';
import './App.css'; 

interface CheckResult {
  status: string;
  is_compromised: boolean;
  count: number;
  message: string;
  recommendation: string;
}

function App() {
  const [credential, setCredential] = useState('');
  const [result, setResult] = useState<CheckResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const BACKEND_URL = 'http://127.0.0.1:5000/check-password';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setError(null);

    if (credential.length === 0) {
        setError("Por favor, insira uma senha ou credencial para verificar.");
        setLoading(false);
        return;
    }

    try {
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ credential: credential }),
      });

      const data: CheckResult = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Erro desconhecido ao verificar a senha.');
      }

      setResult(data);

    } catch (err) {
      if (err instanceof Error) {
          setError(err.message);
      } else {
          setError("Falha ao comunicar com o servidor de backend.");
      }
    } finally {
      setLoading(false);
    }
  };

  const getResultStyle = () => {
    if (!result) return {};
    const color = result.is_compromised ? '#ff4d4f' : '#52c41a';
    return { borderLeft: `5px solid ${color}`, paddingLeft: '15px', color: color }; 
  };

  return (
    <div className="App" style={{ maxWidth: '700px', margin: '50px auto', padding: '25px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{color: '#007bff'}}>PhishingGuard AI</h1>
      <p style={{color: '#666'}}>Verifique se sua credencial foi vazada e receba recomendações de segurança baseadas em IA.</p>

      <form onSubmit={handleSubmit} style={{ margin: '30px 0', display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={credential}
          onChange={(e) => setCredential(e.target.value)}
          placeholder="Insira a senha ou e-mail para verificação"
          disabled={loading}
          style={{ padding: '12px', flexGrow: 1, border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <button type="submit" disabled={loading} style={{ 
            padding: '12px 25px', 
            backgroundColor: loading ? '#ccc' : '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
        }}>
          {loading ? 'Verificando...' : 'Verificar'}
        </button>
      </form>

      {error && (
        <div style={{ color: 'white', backgroundColor: '#ff4d4f', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
          <strong>Falha na Verificação:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{...getResultStyle(), border: '1px solid #eee', padding: '20px', borderRadius: '5px', textAlign: 'left', marginTop: '30px' }}>
          <h2 style={{ marginBottom: '10px', fontSize: '1.5em', color: result.is_compromised ? '#ff4d4f' : '#52c41a' }}>
            {result.is_compromised ? '🚨 CREDENCIAL COMPROMETIDA' : '✅ CREDENCIAL SEGURA'}
          </h2>

          <p style={{ marginBottom: '15px', fontWeight: 'bold' }}>{result.message}</p>

          <div style={{ background: '#f0f2f5', padding: '15px', borderRadius: '5px', marginTop: '20px' }}>
            <h4 style={{ margin: '0 0 10px 0', color: '#007bff' }}>{result.is_compromised ? 'Instruções de Ação Imediata:' : 'Boas Práticas de Segurança:'}</h4>
            <p>{result.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;