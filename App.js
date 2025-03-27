import React, { useState } from 'react';
import './App.css';

function App() {
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    relationName: 'CONFERENCE_REVIEWS',
    attributes: 'paper_id,title,abstract,pdf_path,author_names,author_emails,author_affiliations,pc_member_id,pc_member_name,pc_member_email,review_id,review_comment,review_recommendation,review_date',
    fds: [
      { left: 'paper_id', right: 'title,abstract,pdf_path' },
      { left: 'paper_id,author_position', right: 'author_names,author_emails,author_affiliations' },
      { left: 'pc_member_id', right: 'pc_member_name,pc_member_email' },
      { left: 'review_id', right: 'paper_id,pc_member_id,review_comment,review_recommendation,review_date' }
    ]
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:5000/api/normalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <div className="app">
      <h1>Conference DB Normalization Tool</h1>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Relation Name:</label>
          <input 
            value={formData.relationName}
            onChange={(e) => setFormData({...formData, relationName: e.target.value})}
          />
        </div>
        
        <div className="form-group">
          <label>Attributes (comma separated):</label>
          <textarea
            value={formData.attributes}
            onChange={(e) => setFormData({...formData, attributes: e.target.value})}
            rows={5}
          />
        </div>
        
        <div className="fds-section">
          <h3>Functional Dependencies</h3>
          {formData.fds.map((fd, index) => (
            <div key={index} className="fd-row">
              <input
                value={fd.left}
                onChange={(e) => {
                  const newFds = [...formData.fds];
                  newFds[index].left = e.target.value;
                  setFormData({...formData, fds: newFds});
                }}
                placeholder="Left side"
              />
              <span>→</span>
              <input
                value={fd.right}
                onChange={(e) => {
                  const newFds = [...formData.fds];
                  newFds[index].right = e.target.value;
                  setFormData({...formData, fds: newFds});
                }}
                placeholder="Right side"
              />
              <button 
                type="button" 
                onClick={() => {
                  const newFds = formData.fds.filter((_, i) => i !== index);
                  setFormData({...formData, fds: newFds});
                }}
              >
                Remove
              </button>
            </div>
          ))}
          <button 
            type="button"
            onClick={() => setFormData({
              ...formData, 
              fds: [...formData.fds, { left: '', right: '' }]
            })}
          >
            Add FD
          </button>
        </div>
        
        <button type="submit">Normalize</button>
      </form>
      
      {result && (
        <div className="result">
          <h2>Normalization Steps</h2>
          {result.steps.map((step, i) => (
            <div key={i} className="step">
              <h3>{step.name}</h3>
              <div className="relations">
                {step.relations.map((rel, j) => (
                  <div key={j} className="relation">
                    <h4>{rel.name}</h4>
                    <p>{rel.attributes.join(', ')}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;