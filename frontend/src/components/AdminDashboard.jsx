import { useState, useEffect } from 'react'
import {
  getDepartments,
  createDepartment,
  getDegrees,
  createDegree,
  getStudents,
  getStaff,
  registerStaff,
  getFaceRegistry,
  setStudentClassTeacher,
  trainModel,
  getAttendance,
  exportAttendance,
  getCampus,
  setCampus,
  getStudentRecord,
  getStaffRecord,
} from '../api'
import FaceRegistration from './FaceRegistration'

export default function AdminDashboard({ user }) {
  const [activeTab, setActiveTab] = useState('students')
  const [departments, setDepartments] = useState([])
  const [degrees, setDegrees] = useState([])
  const [students, setStudents] = useState([])
  const [staff, setStaff] = useState([])
  const [registry, setRegistry] = useState([])
  const [attendance, setAttendance] = useState([])
  const [campus, setCampusState] = useState(null)
  const [msg, setMsg] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [faceRegUser, setFaceRegUser] = useState(null)
  const [recordView, setRecordView] = useState(null) // { type: 'student'|'staff', id }
  const [newDeptName, setNewDeptName] = useState('')
  const [newDegreeName, setNewDegreeName] = useState('')
  const [newStaff, setNewStaff] = useState({ first_name: '', last_name: '', email: '', password: '', department_id: '' })

  const load = async () => {
    try {
      const [d, g, st, sf, r, a, camp] = await Promise.all([
        getDepartments(),
        getDegrees(),
        getStudents('admin', null),
        getStaff(),
        getFaceRegistry(),
        getAttendance(date, 'admin'),
        getCampus(),
      ])
      setDepartments(d)
      setDegrees(g)
      setStudents(st)
      setStaff(sf)
      setRegistry(r)
      setAttendance(a)
      setCampusState(camp)
    } catch (e) {
      setMsg(e.message)
    }
  }

  useEffect(() => { load() }, [date])

  if (faceRegUser) {
    return (
      <FaceRegistration
        user={faceRegUser}
        onDone={() => { setFaceRegUser(null); load() }}
      />
    )
  }

  if (recordView) {
    const RecordDetail = () => {
      const [rec, setRec] = useState(null)
      useEffect(() => {
        if (recordView.type === 'student') getStudentRecord(recordView.id).then(setRec)
        else getStaffRecord(recordView.id).then(setRec)
      }, [recordView])
      if (!rec) return <p>Loading...</p>
      return (
        <div className="card">
          <button className="btn" onClick={() => setRecordView(null)} style={{ marginBottom: '1rem' }}>← Back</button>
          <h2>{recordView.type === 'student' ? 'Student' : 'Staff'} Record</h2>
          <p><strong>Name:</strong> {rec.first_name} {rec.last_name}</p>
          <p><strong>Email:</strong> {rec.email}</p>
          <p><strong>Phone:</strong> {rec.phone}</p>
          {rec.department_name && <p><strong>Department:</strong> {rec.department_name}</p>}
          <p><strong>Face registered:</strong> {rec.face_samples || 0} samples</p>
          <p><strong>Location:</strong> {rec.latitude != null ? `${rec.latitude.toFixed(4)}, ${rec.longitude.toFixed(4)}` : 'Not set'}</p>
        </div>
      )
    }
    return <RecordDetail />
  }

  const tabs = ['students', 'staff', 'verify', 'registry', 'attendance', 'campus', 'export']
  return (
    <div>
      <div className="flex-between" style={{ marginBottom: '1.5rem' }}>
        <h2>Admin Dashboard</h2>
        <div className="tabs">
          {tabs.map((t) => (
            <button key={t} className={activeTab === t ? 'active' : ''} onClick={() => setActiveTab(t)}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>
      {msg && <p className="msg info">{msg}</p>}

      {activeTab === 'students' && (
        <div className="card">
          <h3>All Students</h3>
          <table>
            <thead>
              <tr><th>Name</th><th>Email</th><th>Department</th><th>Degree</th><th>Year</th><th>Class teacher</th><th>Action</th></tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.user_id}>
                  <td>{s.first_name} {s.last_name}</td>
                  <td>{s.email}</td>
                  <td>{s.department_name || '-'}</td>
                  <td>{s.degree_name || '-'}</td>
                  <td>{s.year_of_study || '-'}</td>
                  <td>{s.class_teacher_name || '-'}</td>
                  <td>
                    <button className="btn" onClick={() => setRecordView({ type: 'student', id: s.user_id })}>View</button>
                    <button className="btn" onClick={() => setFaceRegUser({ id: s.user_id, name: `${s.first_name} ${s.last_name}` })}>Face</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'staff' && (
        <div className="card">
          <h3>All Staff</h3>

          <div className="card" style={{ margin: '1rem 0' }}>
            <h4>Quick add staff</h4>
            <p className="msg info">Minimal details for new staff. For full profile, staff can later update from registration.</p>
            <div className="flex" style={{ gap: '0.75rem', flexWrap: 'wrap' }}>
              <input
                placeholder="First name"
                value={newStaff.first_name}
                onChange={(e) => setNewStaff((s) => ({ ...s, first_name: e.target.value }))}
              />
              <input
                placeholder="Last name"
                value={newStaff.last_name}
                onChange={(e) => setNewStaff((s) => ({ ...s, last_name: e.target.value }))}
              />
              <input
                placeholder="Email"
                type="email"
                value={newStaff.email}
                onChange={(e) => setNewStaff((s) => ({ ...s, email: e.target.value }))}
              />
              <input
                placeholder="Password"
                type="password"
                value={newStaff.password}
                onChange={(e) => setNewStaff((s) => ({ ...s, password: e.target.value }))}
              />
              <select
                value={newStaff.department_id}
                onChange={(e) => setNewStaff((s) => ({ ...s, department_id: e.target.value }))}
              >
                <option value="">Department</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
              <button
                className="btn btn-primary"
                onClick={async () => {
                  try {
                    if (!newStaff.first_name || !newStaff.last_name || !newStaff.email) {
                      setMsg('First name, last name, email required')
                      return
                    }
                    const payload = {
                      ...newStaff,
                      department_id: newStaff.department_id ? parseInt(newStaff.department_id) : null,
                      accept_rules: true,
                      accept_face_recognition: true,
                      location_permission: true,
                    }
                    await registerStaff(payload)
                    setMsg('Staff added')
                    setNewStaff({ first_name: '', last_name: '', email: '', password: '', department_id: '' })
                    load()
                  } catch (e) {
                    setMsg(e.message)
                  }
                }}
              >
                Add Staff
              </button>
            </div>
          </div>

          <table>
            <thead>
              <tr><th>Name</th><th>Email</th><th>Department</th><th>Action</th></tr>
            </thead>
            <tbody>
              {staff.map((s) => (
                <tr key={s.user_id}>
                  <td>{s.first_name} {s.last_name}</td>
                  <td>{s.email}</td>
                  <td>{s.department_name || '-'}</td>
                  <td>
                    <button className="btn" onClick={() => setRecordView({ type: 'staff', id: s.user_id })}>View</button>
                    <button className="btn" onClick={() => setFaceRegUser({ id: s.user_id, name: `${s.first_name} ${s.last_name}` })}>Face</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'verify' && (
        <div className="card">
          <h3>Verify &amp; Assign Class Teacher</h3>
          <p className="msg info">Correct student–class teacher assignment. Select student and assign staff.</p>
          <table>
            <thead>
              <tr><th>Student</th><th>Current class teacher</th><th>Assign</th></tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.user_id}>
                  <td>{s.first_name} {s.last_name}</td>
                  <td>{s.class_teacher_name || 'None'}</td>
                  <td>
                    <select
                      value={s.class_teacher_id || ''}
                      onChange={async (e) => {
                        const v = e.target.value
                        try {
                          await setStudentClassTeacher(s.user_id, v ? parseInt(v) : null)
                          setMsg('Updated')
                          load()
                        } catch (err) {
                          setMsg(err.message)
                        }
                      }}
                    >
                      <option value="">None</option>
                      {staff.map((st) => <option key={st.user_id} value={st.user_id}>{st.first_name} {st.last_name}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'registry' && (
        <div className="card">
          <h3>Face Registry &amp; Location</h3>
          <button className="btn btn-primary" onClick={async () => { try { await trainModel(); setMsg('Model trained'); load() } catch (e) { setMsg(e.message) } }} style={{ marginBottom: '1rem' }}>Train Model</button>
          <table>
            <thead>
              <tr><th>Name</th><th>Email</th><th>Role</th><th>Samples</th><th>Location</th><th>Action</th></tr>
            </thead>
            <tbody>
              {registry.map((r) => (
                <tr key={r.user_id}>
                  <td>{r.name}</td>
                  <td>{r.email}</td>
                  <td>{r.role}</td>
                  <td>{r.samples_count}</td>
                  <td>{r.latitude != null ? `${r.latitude?.toFixed(4)}, ${r.longitude?.toFixed(4)}` : '-'}</td>
                  <td><button className="btn" onClick={() => setFaceRegUser({ id: r.user_id, name: r.name })}>Re-register</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'attendance' && (
        <div className="card">
          <h3>Attendance (all)</h3>
          <div className="flex-between" style={{ marginBottom: '1rem' }}>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <table>
            <thead>
              <tr><th>Name</th><th>IN</th><th>OUT</th><th>Status</th></tr>
            </thead>
            <tbody>
              {attendance.map((a) => (
                <tr key={a.id}>
                  <td>{a.name ?? (a.first_name + ' ' + a.last_name)}</td>
                  <td>{a.in_time || '-'}</td>
                  <td>{a.out_time || '-'}</td>
                  <td>{a.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'campus' && (
        <div className="card">
          <h3>Campus Boundary</h3>
          {campus && <p>Current: ({campus.center_lat}, {campus.center_lon}) radius {campus.radius_meters}m</p>}
          <CampusForm onSave={async (lat, lon, radius) => { await setCampus(lat, lon, radius); setMsg('Campus updated'); load() }} />
        </div>
      )}

      {activeTab === 'export' && (
        <div className="card">
          <h3>Export Attendance</h3>
          <div className="flex-between" style={{ marginBottom: '1rem' }}>
            <input type="date" id="expStart" />
            <input type="date" id="expEnd" />
            <button className="btn btn-primary" onClick={async () => {
              const start = document.getElementById('expStart').value || date
              const end = document.getElementById('expEnd').value || date
              try {
                await exportAttendance('admin', user.id, start, end, 'students')
                setMsg('Students export downloaded')
              } catch (e) { setMsg(e.message) }
            }}>Export Students</button>
            <button className="btn btn-primary" onClick={async () => {
              const start = document.getElementById('expStart').value || date
              const end = document.getElementById('expEnd').value || date
              try {
                await exportAttendance('admin', user.id, start, end, 'staff')
                setMsg('Staff export downloaded')
              } catch (e) { setMsg(e.message) }
            }}>Export Staff</button>
          </div>
          <p className="msg info">Use custom dates for day / week / month / custom range.</p>
        </div>
      )}

      {/* Departments & Degrees quick add - show only on Students & Staff tabs */}
      {(activeTab === 'students' || activeTab === 'staff') && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>Add Department / Degree</h3>
          <div className="flex" style={{ gap: '1rem', flexWrap: 'wrap' }}>
            <input placeholder="Department name" value={newDeptName} onChange={(e) => setNewDeptName(e.target.value)} />
            <button className="btn btn-primary" onClick={async () => { try { await createDepartment(newDeptName); setNewDeptName(''); load(); setMsg('Department added') } catch (e) { setMsg(e.message) } }}>Add Department</button>
            <input placeholder="Degree name" value={newDegreeName} onChange={(e) => setNewDegreeName(e.target.value)} />
            <button className="btn btn-primary" onClick={async () => { try { await createDegree(newDegreeName); setNewDegreeName(''); load(); setMsg('Degree added') } catch (e) { setMsg(e.message) } }}>Add Degree</button>
          </div>
        </div>
      )}
    </div>
  )
}

function CampusForm({ onSave }) {
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')
  const [radius, setRadius] = useState(500)
  const useCurrent = () => {
    navigator.geolocation.getCurrentPosition((p) => { setLat(p.coords.latitude.toString()); setLon(p.coords.longitude.toString()) }, () => {})
  }
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(parseFloat(lat), parseFloat(lon), radius) }}>
      <div className="form-group"><label>Latitude</label><input type="number" step="any" value={lat} onChange={(e) => setLat(e.target.value)} required /></div>
      <div className="form-group"><label>Longitude</label><input type="number" step="any" value={lon} onChange={(e) => setLon(e.target.value)} required /></div>
      <button type="button" className="btn" onClick={useCurrent}>Use current location</button>
      <div className="form-group" style={{ marginTop: '1rem' }}><label>Radius (m)</label><input type="number" value={radius} onChange={(e) => setRadius(Number(e.target.value))} /></div>
      <button type="submit" className="btn btn-primary">Save Campus</button>
    </form>
  )
}
