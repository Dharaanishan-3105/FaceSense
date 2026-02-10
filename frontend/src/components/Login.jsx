import { useState } from 'react'
import { login } from '../api'
import StudentRegister from './StudentRegister'
import StaffRegister from './StaffRegister'
import './Login.css'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState('login') // 'login' | 'student' | 'staff'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      onLogin(data.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (mode === 'student') return <StudentRegister onBack={() => setMode('login')} onDone={() => setMode('login')} />
  if (mode === 'staff') return <StaffRegister onBack={() => setMode('login')} onDone={() => setMode('login')} />

  return (
    <div className="login-page">
      <div className="login-box">
        <h1>FaceSense</h1>
        <p className="login-subtitle">Smart face recognition attendance</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="msg error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <div className="login-register-links">
          <button type="button" className="link-btn" onClick={() => setMode('student')}>Register as Student</button>
          <span>|</span>
          <button type="button" className="link-btn" onClick={() => setMode('staff')}>Register as Staff</button>
        </div>
      </div>
    </div>
  )
}
