import { useState, useEffect } from 'react'

function Questionnaire() {
  // Form state
  const [gender, setGender] = useState('')
  const [height, setHeight] = useState('')
  const [armSpan, setArmSpan] = useState('')
  const [climbedProblems, setClimbedProblems] = useState([])
  const [preferredTags, setPreferredTags] = useState([])
  
  // Options
  const [availableTags, setAvailableTags] = useState([])
  const [problemSearch, setProblemSearch] = useState('')
  const [problemResults, setProblemResults] = useState([])
  
  // Load available tags on mount
  useEffect(() => {
    fetch('http://localhost:8000/api/questionnaire/available-tags')
      .then(res => res.json())
      .then(data => setAvailableTags(data))
  }, [])
  
  // Search problems as user types
  useEffect(() => {
    if (problemSearch.length > 2) {
      fetch(`http://localhost:8000/api/questionnaire/search-problems?q=${problemSearch}`)
        .then(res => res.json())
        .then(data => setProblemResults(data))
    } else {
      setProblemResults([])
    }
  }, [problemSearch])
  
  const addProblem = (problem) => {
    if (!climbedProblems.find(p => p.id === problem.id)) {
      setClimbedProblems([...climbedProblems, problem])
    }
    setProblemSearch('')
    setProblemResults([])
  }
  
  const removeProblem = (problemId) => {
    setClimbedProblems(climbedProblems.filter(p => p.id !== problemId))
  }
  
  const toggleTag = (tag) => {
    if (preferredTags.includes(tag)) {
      setPreferredTags(preferredTags.filter(t => t !== tag))
    } else {
      setPreferredTags([...preferredTags, tag])
    }
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const submission = {
      gender: gender || null,
      height: height ? parseInt(height) : null,
      arm_span: armSpan ? parseInt(armSpan) : null,
      climbed_problem_ids: climbedProblems.map(p => p.id),
      preferred_tags: preferredTags
    }
    
    const response = await fetch('http://localhost:8000/api/questionnaire/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(submission)
    })
    
    if (response.ok) {
      alert('Thank you! Your response has been submitted.')
      // Reset form
      setGender('')
      setHeight('')
      setArmSpan('')
      setClimbedProblems([])
      setPreferredTags([])
    }
  }
  
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Climbing Questionnaire</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Demographics */}
        <div>
          <label className="block mb-2 font-semibold">Gender (optional)</label>
          <select 
            value={gender} 
            onChange={(e) => setGender(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">Prefer not to say</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        <div>
          <label className="block mb-2 font-semibold">Height (cm, optional)</label>
          <input 
            type="number" 
            value={height}
            onChange={(e) => setHeight(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="170"
          />
        </div>
        
        <div>
          <label className="block mb-2 font-semibold">Arm Span (cm, optional)</label>
          <input 
            type="number" 
            value={armSpan}
            onChange={(e) => setArmSpan(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="175"
          />
        </div>
        
        {/* Climbed Problems */}
        <div>
          <label className="block mb-2 font-semibold">Problems You've Topped</label>
          <input 
            type="text"
            value={problemSearch}
            onChange={(e) => setProblemSearch(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="Search for problems..."
          />
          
          {/* Search results */}
          {problemResults.length > 0 && (
            <div className="border rounded mt-2 max-h-60 overflow-y-auto">
              {problemResults.map(problem => (
                <div 
                  key={problem.id}
                  onClick={() => addProblem(problem)}
                  className="p-2 hover:bg-gray-100 cursor-pointer"
                >
                  <strong>{problem.name}</strong> ({problem.grade}) - {problem.sector.name}
                </div>
              ))}
            </div>
          )}
          
          {/* Selected problems */}
          <div className="mt-4 space-y-2">
            {climbedProblems.map(problem => (
              <div key={problem.id} className="flex items-center justify-between bg-green-100 p-2 rounded">
                <span><strong>{problem.name}</strong> ({problem.grade})</span>
                <button 
                  type="button"
                  onClick={() => removeProblem(problem.id)}
                  className="text-red-600 font-bold"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
        
        {/* Preferred Tags */}
        <div>
          <label className="block mb-2 font-semibold">Preferred Climbing Styles</label>
          <div className="flex flex-wrap gap-2">
            {availableTags.map(({tag, count}) => (
              <button
                key={tag}
                type="button"
                onClick={() => toggleTag(tag)}
                className={`px-3 py-1 rounded ${
                  preferredTags.includes(tag)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200'
                }`}
              >
                {tag} ({count})
              </button>
            ))}
          </div>
        </div>
        
        {/* Submit */}
        <button 
          type="submit"
          className="w-full bg-green-500 text-white py-3 rounded font-bold hover:bg-green-600"
        >
          Submit Questionnaire
        </button>
      </form>
    </div>
  )
}

export default Questionnaire