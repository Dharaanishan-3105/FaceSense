import { useState, useEffect } from 'react'
import './App.css'
import Login from './components/Login'
import AdminDashboard from './components/AdminDashboard'
import TeacherDashboard from './components/TeacherDashboard'
import AttendanceKiosk from './components/AttendanceKiosk'

function App() {
  const [user, setUser] = useState(null)
  const [page, setPage] = useState('attendance')

  useEffect(() => {
    const stored = localStorage.getItem('facesense_user')
    if (stored) {
      try {
        setUser(JSON.parse(stored))
      } catch (_) {}
    }
  }, [])

  const handleLogin = (u) => {
    setUser(u)
    localStorage.setItem('facesense_user', JSON.stringify(u))
    setPage(u.role === 'admin' ? 'admin' : u.role === 'staff' ? 'teacher' : 'attendance')
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('facesense_user')
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="app-layout">
      <header className="header">
        <h1>FaceSense</h1>
        <nav>
          {user.role === 'admin' && (
            <a href="#" onClick={(e) => { e.preventDefault(); setPage('admin') }}>Admin</a>
          )}
          {user.role === 'staff' && (
            <a href="#" onClick={(e) => { e.preventDefault(); setPage('teacher') }}>My Class</a>
          )}
          <a href="#" onClick={(e) => { e.preventDefault(); setPage('attendance') }}>Attendance</a>
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </header>
      <main className="main">
        {page === 'admin' && <AdminDashboard user={user} />}
        {page === 'teacher' && <TeacherDashboard user={user} />}
        {page === 'attendance' && <AttendanceKiosk user={user} />}
      </main>
    </div>
  )
}

export default App
