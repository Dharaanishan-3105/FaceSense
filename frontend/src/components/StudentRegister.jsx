import { useState, useEffect } from 'react'
import { getDepartments, getDegrees, getStaff, uploadIdCard, registerStudent } from '../api'

export default function StudentRegister({ onBack, onDone }) {
  const [departments, setDepartments] = useState([])
  const [degrees, setDegrees] = useState([])
  const [staffList, setStaffList] = useState([])
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    first_name: '', last_name: '', father_name: '', mother_name: '', phone: '', email: '', password: '',
    parents_number: '', id_card_path: '', hair_colour: '', eye_colour: '', blood_group: '',
    year_of_study: '', semester: '', department_id: '', degree_id: '', hod_name: '', class_teacher_id: '',
    shift_type: 'full_time', shift_time: 'morning',
    accept_rules: true, accept_face_recognition: true, location_permission: true,
  })

  useEffect(() => {
    Promise.all([getDepartments(), getDegrees(), getStaff()]).then(([d, g, s]) => {
      setDepartments(d)
      setDegrees(g)
      setStaffList(s)
    }).catch(() => setMsg('Failed to load options'))
  }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleFile = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const { path } = await uploadIdCard(file)
      setForm((prev) => ({ ...prev, id_card_path: path }))
      setMsg('ID card uploaded')
    } catch (err) {
      setMsg(err.message)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMsg('')
    setLoading(true)
    try {
      const payload = { ...form }
      if (payload.department_id) payload.department_id = parseInt(payload.department_id)
      if (payload.degree_id) payload.degree_id = parseInt(payload.degree_id)
      if (payload.year_of_study) payload.year_of_study = parseInt(payload.year_of_study)
      if (payload.semester) payload.semester = parseInt(payload.semester)
      if (payload.class_teacher_id) payload.class_teacher_id = parseInt(payload.class_teacher_id)
      await registerStudent(payload)
      setMsg('Registration successful! You can now login and complete face registration.')
      setTimeout(() => onDone(), 2000)
    } catch (err) {
      setMsg(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-box" style={{ maxWidth: '600px' }}>
        <div className="header-with-back">
          <button type="button" className="icon-back" onClick={onBack}>←</button>
          <h1>Student Registration</h1>
        </div>
        <p className="login-subtitle">First-time registration – complete all sections</p>
        {msg && <p className={msg.includes('success') ? 'msg success' : 'msg error'}>{msg}</p>}
        <form onSubmit={handleSubmit} className="registration-form">
          <section>
            <h4>Name &amp; Family</h4>
            <div className="grid-2">
              <div className="form-group">
                <label>First name *</label>
                <input name="first_name" value={form.first_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Last name *</label>
                <input name="last_name" value={form.last_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Father&apos;s name</label>
                <input name="father_name" value={form.father_name} onChange={handleChange} />
              </div>
              <div className="form-group">
                <label>Mother&apos;s name</label>
                <input name="mother_name" value={form.mother_name} onChange={handleChange} />
              </div>
            </div>
          </section>
          <section>
            <h4>Contact</h4>
            <div className="grid-2">
              <div className="form-group">
                <label>Phone *</label>
                <input name="phone" type="tel" value={form.phone} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input name="email" type="email" value={form.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Parents number *</label>
                <input name="parents_number" value={form.parents_number} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Password *</label>
                <input name="password" type="password" value={form.password} onChange={handleChange} required />
              </div>
            </div>
          </section>
          <section>
            <h4>College ID &amp; Physical</h4>
            <div className="form-group">
              <label>Upload college ID card *</label>
              <input type="file" accept=".jpg,.jpeg,.png,.pdf" onChange={handleFile} required />
              {form.id_card_path && <span className="msg info">Uploaded</span>}
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label>Hair colour *</label>
                <input name="hair_colour" value={form.hair_colour} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Eye colour *</label>
                <input name="eye_colour" value={form.eye_colour} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Blood group *</label>
                <input name="blood_group" value={form.blood_group} onChange={handleChange} placeholder="e.g. O+ " required />
              </div>
            </div>
          </section>
          <section>
            <h4>Academic</h4>
            <div className="grid-2">
              <div className="form-group">
                <label>Year of study *</label>
                <input name="year_of_study" type="number" min="1" value={form.year_of_study} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Semester *</label>
                <input name="semester" type="number" min="1" value={form.semester} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Department *</label>
                <select name="department_id" value={form.department_id} onChange={handleChange} required>
                  <option value="">Select</option>
                  {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Degree *</label>
                <select name="degree_id" value={form.degree_id} onChange={handleChange} required>
                  <option value="">Select</option>
                  {degrees.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>HOD name *</label>
                <input name="hod_name" value={form.hod_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Class teacher (staff) *</label>
                <select name="class_teacher_id" value={form.class_teacher_id} onChange={handleChange} required>
                  <option value="">Select</option>
                  {staffList.map((s) => <option key={s.user_id} value={s.user_id}>{s.first_name} {s.last_name}</option>)}
                </select>
              </div>
            </div>
          </section>
          <section>
            <h4>Shift</h4>
            <div className="grid-2">
              <div className="form-group">
                <label>Shift type</label>
                <select name="shift_type" value={form.shift_type} onChange={handleChange}>
                  <option value="full_time">Full time</option>
                  <option value="part_time">Part time</option>
                </select>
              </div>
              <div className="form-group">
                <label>Shift time</label>
                <select name="shift_time" value={form.shift_time} onChange={handleChange}>
                  <option value="morning">Morning</option>
                  <option value="afternoon">Afternoon</option>
                </select>
              </div>
            </div>
          </section>
          <section>
            <h4>Acceptances</h4>
            <div className="checkbox-group">
              <input type="checkbox" name="accept_rules" id="ar" checked={form.accept_rules} onChange={handleChange} required />
              <label htmlFor="ar">I accept college rules and regulation</label>
            </div>
            <div className="checkbox-group">
              <input type="checkbox" name="accept_face_recognition" id="afr" checked={form.accept_face_recognition} onChange={handleChange} required />
              <label htmlFor="afr">I accept face recognition for attendance</label>
            </div>
            <div className="checkbox-group">
              <input type="checkbox" name="location_permission" id="lp" checked={form.location_permission} onChange={handleChange} required />
              <label htmlFor="lp">I give permission to access location (campus); attendance only when face and location match</label>
            </div>
          </section>
          <div className="flex-between" style={{ marginTop: '1rem' }}>
            <button type="button" className="btn" onClick={onBack}>Back</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>{loading ? 'Submitting...' : 'Register'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
