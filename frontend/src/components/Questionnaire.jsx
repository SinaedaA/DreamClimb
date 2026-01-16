import FingerprintJS from '@fingerprintjs/fingerprintjs'
import { useState, useEffect } from 'react'
import { CLIMBING_TAGS } from '../data/climbingTags'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function Questionnaire() {
  // Submission state
  const [showSuccess, setShowSuccess] = useState(false)
  const [userUpdateCode, setUserUpdateCode] = useState('')
  const [subscribeNewsletter, setSubscribeNewsletter] = useState(false)
  // User identification
  const [browserId, setBrowserId] = useState(null)
  const [email, setEmail] = useState('')
  
  // Form state
  const [gender, setGender] = useState('')
  const [height, setHeight] = useState('')
  const [armSpan, setArmSpan] = useState('')
  const [climbedProblems, setClimbedProblems] = useState([])
  const [preferredTags, setPreferredTags] = useState([])
  
  // Options
  const [availableTags] = useState(CLIMBING_TAGS) // Hardcoded tags
  const [problemSearch, setProblemSearch] = useState('')
  const [problemResults, setProblemResults] = useState([])
  
  // Get browser fingerprint on mount
  useEffect(() => {
    const getFingerprint = async () => {
      try {
        const fp = await FingerprintJS.load()
        const result = await fp.get()
        setBrowserId(result.visitorId)
        console.log('Browser ID:', result.visitorId)
      } catch (error) {
        console.error('Error getting fingerprint:', error)
      }
    }
    getFingerprint()
  }, [])
  
  // Search problems as user types
  useEffect(() => {
    if (problemSearch.length > 2) {
      fetch(`${API_URL}/questionnaire/search-problems?q=${problemSearch}`)
        .then(res => res.json())
        .then(data => setProblemResults(data))
        .catch(err => console.error('Error searching problems:', err))
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
  
  const toggleTag = (tagOriginal) => {
    // Store the French tag (tag_original) for submission
    if (preferredTags.includes(tagOriginal)) {
      setPreferredTags(preferredTags.filter(t => t !== tagOriginal))
    } else {
      setPreferredTags([...preferredTags, tagOriginal])
    }
  }
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const submission = {
      // Identification
      browser_id: browserId,
      email: email || null,
      update_code: null,
      
      // Demographics
      gender: gender || null,
      height: height ? parseInt(height) : null,
      arm_span: armSpan ? parseInt(armSpan) : null,
      
      // Climbing data
      climbed_problem_ids: climbedProblems.map(p => p.id),
      preferred_tags: preferredTags, // French tags
      subscribe_newsletter: subscribeNewsletter,
    }
    
    try {
      const response = await fetch(`${API_URL}/questionnaire/submit`, {
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
        setEmail('')
      } else {
        alert('Error submitting response. Please try again.')
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Error submitting response. Please try again.')
    }
  }
  
  return (
    <>
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="text-3xl font-bold mb-6">DreamClimb Survey</h1>
        <p className="mb-6 text-left text-body md:text-l">
          To help us improve the DreamClimb boulder recommendation system, please fill out this short survey about the problems
          you've topped in Fontainebleau, and your preferred climbing styles. <br/><br/>
          We also collect some basic climber characteristics (all optional), such as <b>gender</b>, <b>height</b>, and <b>arm span</b>.
          These will help the model recommend problems that suit each and everyone's physique, based on other users' experience!
          Your data will be anonymized and used solely for research purposes, and system improvement.
        </p>  
        
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
          <label className="block mb-2 font-semibold">Update code (if you have one)</label>
          <input 
            type="string" 
            value={userUpdateCode}
            onChange={(e) => setUserUpdateCode(e.target.value)}
            className="w-full p-2 border rounded"
          />
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
            {availableTags.map(({tag, tag_original, count}) => (
              <button
                key={tag_original}
                type="button"
                onClick={() => toggleTag(tag_original)}
                className={`px-3 py-1 rounded ${
                  preferredTags.includes(tag_original)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200'
                }`}
              >
                {tag} ({count})
              </button>
            ))}
          </div>
        </div>
        
        {/* Optional identification */}
        <div className="border-t pt-4 mt-4">
          <p className="text-sm text-gray-600 mb-3">
            <strong>Want to update your profile later?</strong> (Optional)
          </p>
          
          <label className="block mb-2 text-sm">
            Email address
            <input 
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="climber@example.com"
              className="w-full p-2 border rounded mt-1"
            />
          </label>
          
          {browserId && (
            <p className="text-xs text-gray-500 mt-2">
              Or remember this code: <strong className="font-mono">{browserId.slice(0, 10)}</strong>
            </p>
          )}
          
          <p className="text-xs text-gray-400 mt-3">
            We use anonymous browser fingerprinting to prevent duplicate submissions. 
            No personal data is collected or shared beyond what you provide above.             
          </p>
        </div>
        
        {/* Newsletter Subscription */}
        <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
        <input 
            type="checkbox"
            id="newsletter"
            checked={subscribeNewsletter}
            onChange={(e) => setSubscribeNewsletter(e.target.checked)}
            className="mt-1 h-4 w-4 text-blue-600 rounded focus:ring-blue-500"
        />
        <label htmlFor="newsletter" className="text-sm text-gray-700 cursor-pointer">
            <span className="font-medium">Stay updated!</span>
            <br />
            Receive an email when DreamClimb launches and for future features & improvements.
            If unticked, e-mail addresses will be deleted after initial data collection phase is completed.
        </label>
        </div>

        {/* Submit */}
        <button 
          type="submit"
          className="w-full bg-green-500 text-white py-3 rounded font-bold hover:bg-green-600"
        >
          Submit Survey
        </button>
      </form>
    </div>

    {/* Success Modal */}
    {showSuccess && (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded-lg max-w-md mx-4">
          <h2 className="text-2xl font-bold mb-4">✅ Thank You!</h2>
          <p className="mb-4">Your response has been submitted successfully.</p>
          
          <div className="bg-blue-50 border-2 border-blue-500 p-4 rounded mb-4">
            <p className="font-bold mb-2">📝 Your Update Code:</p>
            <p className="text-3xl font-mono text-center my-4 select-all bg-white p-2 rounded border">
              {userUpdateCode}
            </p>
            <p className="text-sm text-gray-600">
              Save this code to add more problems later!
            </p>
          </div>
          
          <button 
            onClick={() => {
              setShowSuccess(false)
              // Reset form
              setGender('')
              setHeight('')
              setArmSpan('')
              setClimbedProblems([])
              setPreferredTags([])
              setEmail('')
            }}
            className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
          >
            Close
          </button>
        </div>
      </div>
    )}
  </>
  )
}

export default Questionnaire