import { useState, useEffect } from 'react'
import {
  getDepartments,
  getDegrees,
  getStudents,
  getAttendance,
  getAttendanceStats,
  exportAttendance,
  getStudentRecord,
} from '../api'

export default function TeacherDashboard({ user }) {
  const [departments, setDepartments] = useState([])
  const [degrees, setDegrees] = useState([])
  const [students, setStudents] = useState([])
  const [attendance, setAttendance] = useState([])
  const [stats, setStats] = useState({})
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [filters, setFilters] = useState({ degree_id: '', department_id: '', year: '', semester: '' })
  const [range, setRange] = useState('day') // day | week | month | custom
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')
  const [recordView, setRecordView] = useState(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    getDepartments().then(setDepartments).catch(() => {})
    getDegrees().then(setDegrees).catch(() => {})
  }, [])

  const loadStudents = () => {
    const f = {}
    if (filters.degree_id) f.degree_id = parseInt(filters.degree_id)
    if (filters.department_id) f.department_id = parseInt(filters.department_id)
    if (filters.year !== '') f.year = parseInt(filters.year)
    if (filters.semester !== '') f.semester = parseInt(filters.semester)
    getStudents('class_teacher', user.id, f).then(setStudents).catch(() => setMsg('Failed to load'))
  }

  const loadAttendance = () => {
    getAttendance(date, 'class_teacher', user.id).then(setAttendance).catch(() => setAttendance([]))
  }

  useEffect(() => { loadStudents(); loadAttendance() }, [date])
  useEffect(() => { loadStudents() }, [filters.degree_id, filters.department_id, filters.year, filters.semester])

  const getStartEnd = () => {
    const today = new Date().toISOString().slice(0, 10)
    if (range === 'day') return { start: date, end: date }
    if (range === 'week') {
      const d = new Date(date)
      d.setDate(d.getDate() - 7)
      return { start: d.toISOString().slice(0, 10), end: today }
    }
    if (range === 'month') {
      const d = new Date(date)
      d.setMonth(d.getMonth() - 1)
      return { start: d.toISOString().slice(0, 10), end: today }
    }
    return { start: customStart || date, end: customEnd || date }
  }

  const loadStats = () => {
    const { start, end } = getStartEnd()
    getAttendanceStats('class_teacher', user.id, start, end).then(setStats).catch(() => setStats({}))
  }

  useEffect(() => { loadStats() }, [range, date, customStart, customEnd])

  const handleExport = async () => {
    const { start, end } = getStartEnd()
    try {
      await exportAttendance('class_teacher', user.id, start, end)
      setMsg('Excel downloaded')
    } catch (e) {
      setMsg(e.message)
    }
  }

  if (recordView) {
    return (
      <StudentRecordView
        userId={recordView}
        onBack={() => setRecordView(null)}
      />
    )
  }

  return (
    <div>
      <h2>My Class – Attendance</h2>
      {msg && <p className="msg info">{msg}</p>}

      <div className="card">
        <h3>Filters (degree, department, year, semester)</h3>
        <div className="flex" style={{ gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <select value={filters.degree_id} onChange={(e) => setFilters((f) => ({ ...f, degree_id: e.target.value }))}>
            <option value="">All degrees</option>
            {degrees.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <select value={filters.department_id} onChange={(e) => setFilters((f) => ({ ...f, department_id: e.target.value }))}>
            <option value="">All departments</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <input type="number" placeholder="Year" value={filters.year} onChange={(e) => setFilters((f) => ({ ...f, year: e.target.value }))} style={{ width: '80px' }} />
          <input type="number" placeholder="Semester" value={filters.semester} onChange={(e) => setFilters((f) => ({ ...f, semester: e.target.value }))} style={{ width: '90px' }} />
        </div>
        <p className="msg info">Load departments/degrees from Admin first if empty.</p>
      </div>

      <div className="card">
        <h3>My Students</h3>
        <table>
          <thead>
            <tr><th>Name</th><th>Email</th><th>Department</th><th>Degree</th><th>Year</th><th>Semester</th><th>Action</th></tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.user_id}>
                <td>{s.first_name} {s.last_name}</td>
                <td>{s.email}</td>
                <td>{s.department_name || '-'}</td>
                <td>{s.degree_name || '-'}</td>
                <td>{s.year_of_study || '-'}</td>
                <td>{s.semester || '-'}</td>
                <td><button className="btn" onClick={() => setRecordView(s.user_id)}>View record</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {students.length === 0 && <p className="msg info">No students assigned. Ask admin to set you as class teacher.</p>}
      </div>

      <div className="card">
        <h3>Attendance – Day view</h3>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ marginBottom: '1rem' }} />
        <table>
          <thead>
            <tr><th>Name</th><th>IN</th><th>OUT</th><th>Status</th></tr>
          </thead>
          <tbody>
            {attendance.map((a) => (
              <tr key={a.id}>
                <td>{a.first_name} {a.last_name}</td>
                <td>{a.in_time || '-'}</td>
                <td>{a.out_time || '-'}</td>
                <td>{a.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Attendance stats (day / week / month / custom)</h3>
        <div className="flex" style={{ gap: '0.5rem', marginBottom: '1rem' }}>
          {['day', 'week', 'month', 'custom'].map((r) => (
            <button key={r} className={`btn ${range === r ? 'btn-primary' : ''}`} onClick={() => setRange(r)}>{r}</button>
          ))}
          {range === 'custom' && (
            <>
              <input type="date" value={customStart} onChange={(e) => setCustomStart(e.target.value)} />
              <input type="date" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} />
            </>
          )}
        </div>
        <div className="stats-grid">
          {Object.entries(stats).length === 0 ? (
            <p className="msg info">No stats for selected range.</p>
          ) : (
            Object.entries(stats).map(([d, v]) => (
              <div key={d} className="stat-box">
                <div className="value">{v.present + v.partial || 0}</div>
                <div className="label">{d} – present</div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card">
        <h3>Download attendance Excel</h3>
        <p className="msg info">Day, week, month, or custom dates. Includes present, absent, date/time.</p>
        <div className="flex" style={{ gap: '0.5rem', marginBottom: '1rem' }}>
          <button className="btn btn-primary" onClick={() => { setRange('day'); setTimeout(handleExport, 100) }}>Today</button>
          <button className="btn btn-primary" onClick={() => { setRange('week'); setTimeout(handleExport, 100) }}>This week</button>
          <button className="btn btn-primary" onClick={() => { setRange('month'); setTimeout(handleExport, 100) }}>This month</button>
          <button className="btn btn-primary" onClick={handleExport}>Custom range (use above)</button>
        </div>
      </div>
    </div>
  )
}

function StudentRecordView({ userId, onBack }) {
  const [rec, setRec] = useState(null)
  useEffect(() => {
    getStudentRecord(userId).then(setRec).catch(() => setRec(null))
  }, [userId])
  if (!rec) return <div className="card"><p>Loading...</p><button className="btn" onClick={onBack}>Back</button></div>
  return (
    <div className="card">
      <button className="btn" onClick={onBack} style={{ marginBottom: '1rem' }}>← Back</button>
      <h2>Student record</h2>
      <p><strong>Name:</strong> {rec.first_name} {rec.last_name}</p>
      <p><strong>Email:</strong> {rec.email}</p>
      <p><strong>Phone:</strong> {rec.phone}</p>
      <p><strong>Department:</strong> {rec.department_name || '-'}</p>
      <p><strong>Degree:</strong> {rec.degree_name || '-'}</p>
      <p><strong>Year / Semester:</strong> {rec.year_of_study} / {rec.semester}</p>
      <p><strong>Face samples:</strong> {rec.face_samples || 0}</p>
      <p><strong>Location:</strong> {rec.latitude != null ? `${rec.latitude?.toFixed(4)}, ${rec.longitude?.toFixed(4)}` : 'Not set'}</p>
    </div>
  )
}
