import React, { useMemo, useState } from 'react';
import Editor from '@monaco-editor/react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '0 B';
  const sizes = ['B', 'KB', 'MB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  return `${(bytes / 1024 ** i).toFixed(1)} ${sizes[i]}`;
};

export default function App() {
  const [files, setFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [editorValue, setEditorValue] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [llmQuestion, setLlmQuestion] = useState('');
  const [llmResponse, setLlmResponse] = useState('');
  const [status, setStatus] = useState('');

  const handleFileSelect = async (event) => {
    const selectedFiles = Array.from(event.target.files || []);
    const enrichedFiles = await Promise.all(
      selectedFiles.map(async (file) => {
        const content = await file.text();
        return {
          id: file.webkitRelativePath || file.name,
          name: file.name,
          size: file.size,
          path: file.webkitRelativePath || file.name,
          content,
        };
      })
    );
    setFiles(enrichedFiles);
    if (enrichedFiles.length > 0) {
      setActiveFile(enrichedFiles[0]);
      setEditorValue(enrichedFiles[0].content);
    }
  };

  const indexSelectedFiles = async () => {
    if (files.length === 0) {
      setStatus('No files loaded to index.');
      return;
    }
    setStatus('Indexing files locally...');
    const payload = {
      items: files.map((file) => ({
        doc_id: file.id,
        content: file.content,
        metadata: {
          path: file.path,
          size: file.size,
        },
      })),
    };
    const response = await fetch(`${API_BASE}/add-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    setStatus(`Indexed ${data.indexed} documents.`);
  };

  const runSearch = async () => {
    if (!searchQuery) return;
    setStatus('Searching locally...');
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: searchQuery, top_k: 5 }),
    });
    const data = await response.json();
    setSearchResults(data.results || []);
    setStatus(`Found ${data.results?.length || 0} matches.`);
  };

  const askLlm = async () => {
    if (!llmQuestion) return;
    setStatus('Querying local LLM...');
    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: llmQuestion, top_k: 4 }),
    });
    const data = await response.json();
    setLlmResponse(data.response || '');
    setStatus('LLM response ready.');
  };

  const handleFileClick = (file) => {
    setActiveFile(file);
    setEditorValue(file.content);
  };

  const activeFileLanguage = useMemo(() => {
    if (!activeFile) return 'plaintext';
    const parts = activeFile.name.split('.');
    return parts.length > 1 ? parts.at(-1) : 'plaintext';
  }, [activeFile]);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div>
          <h1>LocalForge</h1>
          <p>Offline-first AI development environment</p>
        </div>
        <div className="status">{status}</div>
      </header>

      <main className="layout">
        <section className="sidebar">
          <div className="panel">
            <h2>Project Files</h2>
            <input
              type="file"
              webkitdirectory="true"
              multiple
              onChange={handleFileSelect}
            />
            <button className="primary" type="button" onClick={indexSelectedFiles}>
              Index in LocalForge
            </button>
            <ul className="file-list">
              {files.map((file) => (
                <li
                  key={file.id}
                  className={activeFile?.id === file.id ? 'active' : ''}
                  onClick={() => handleFileClick(file)}
                >
                  <span>{file.name}</span>
                  <span className="meta">{formatBytes(file.size)}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="editor-panel">
          <div className="panel">
            <h2>{activeFile ? activeFile.name : 'Editor'}</h2>
            <Editor
              height="400px"
              language={activeFileLanguage}
              value={editorValue}
              theme="vs-dark"
              onChange={(value) => setEditorValue(value || '')}
              options={{ minimap: { enabled: false }, fontSize: 13 }}
            />
          </div>

          <div className="panel">
            <h2>Embedding Search</h2>
            <div className="row">
              <input
                type="text"
                placeholder="Search across indexed code..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />
              <button type="button" onClick={runSearch}>
                Search
              </button>
            </div>
            <div className="results">
              {searchResults.map((result) => (
                <div key={result.id} className="result-card">
                  <div className="result-header">
                    <strong>{result.id}</strong>
                    <span>{result.score.toFixed(2)}</span>
                  </div>
                  <div className="result-bar">
                    <span style={{ width: `${Math.min(result.score * 100, 100)}%` }} />
                  </div>
                  <pre>{result.content.slice(0, 180)}...</pre>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="assistant-panel">
          <div className="panel">
            <h2>Local LLM Assistant</h2>
            <textarea
              value={llmQuestion}
              onChange={(event) => setLlmQuestion(event.target.value)}
              placeholder="Ask for a summary, suggestion, or next steps..."
              rows={6}
            />
            <button className="primary" type="button" onClick={askLlm}>
              Ask Local LLM
            </button>
            <div className="response">
              <pre>{llmResponse}</pre>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
