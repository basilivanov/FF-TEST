import React from 'react'

const SimpleTest: React.FC = () => {
  return (
    <div style={{padding: '20px', fontFamily: 'Arial'}}>
      <h1>✅ React Works!</h1>
      <p>Простой тест без зависимостей</p>
      <div style={{background: '#f0f0f0', padding: '10px', margin: '10px 0'}}>
        <h3>📋 Logs Mock Data:</h3>
        <p>✅ Feature generation started</p>
        <p>❌ Code compilation failed</p>
        <p>⚠️ High queue length detected</p>
      </div>
      <div style={{background: '#e0f0ff', padding: '10px', margin: '10px 0'}}>
        <h3>🌐 Call Graph Mock Data:</h3>
        <p>📊 System Dependencies Graph</p>
        <p>🔗 5 nodes: API Router, Orchestrator, Database, LLM Router, Auth</p>
      </div>
    </div>
  )
}

export default SimpleTest