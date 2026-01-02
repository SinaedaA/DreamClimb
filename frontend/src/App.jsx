import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [sectors, setSectors] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch sectors from your API
    fetch('http://localhost:8000/api/sectors')
      .then(res => res.json())
      .then(data => {
        setSectors(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error:', err)
        setLoading(false)
      })
  }, [])

  if (loading) return <div>Loading sectors...</div>

  return (
    <div className="App">
      <h1>Bleau Sectors</h1>
      <ul>
        {sectors.map(sector => (
          <li key={sector.id}>
            <strong>{sector.name}</strong> ({sector.slug}) - {sector.grade_range}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default App