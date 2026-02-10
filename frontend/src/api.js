const API_BASE = '/api';

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  return data;
}

export async function getDepartments() {
  const res = await fetch(`${API_BASE}/departments`);
  const data = await res.json();
  return data.departments || [];
}

export async function createDepartment(name) {
  const res = await fetch(`${API_BASE}/departments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function getDegrees() {
  const res = await fetch(`${API_BASE}/degrees`);
  const data = await res.json();
  return data.degrees || [];
}

export async function createDegree(name) {
  const res = await fetch(`${API_BASE}/degrees`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function uploadIdCard(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/upload-id-card`, { method: 'POST', body: form });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Upload failed');
  return data;
}

export async function registerStudent(payload) {
  const res = await fetch(`${API_BASE}/students/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function registerStaff(payload) {
  const res = await fetch(`${API_BASE}/staff/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function getStudents(role, userId, filters = {}) {
  let url = `${API_BASE}/students?role=${role || ''}&user_id=${userId || ''}`;
  if (filters.degree_id) url += `&degree_id=${filters.degree_id}`;
  if (filters.department_id) url += `&department_id=${filters.department_id}`;
  if (filters.year !== undefined) url += `&year=${filters.year}`;
  if (filters.semester !== undefined) url += `&semester=${filters.semester}`;
  const res = await fetch(url);
  const data = await res.json();
  return data.students || [];
}

export async function getStaff() {
  const res = await fetch(`${API_BASE}/staff`);
  const data = await res.json();
  return data.staff || [];
}

export async function updateStudent(userId, payload) {
  const res = await fetch(`${API_BASE}/students/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function updateStaff(userId, payload) {
  const res = await fetch(`${API_BASE}/staff/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function setStudentClassTeacher(userId, classTeacherId) {
  const res = await fetch(`${API_BASE}/students/${userId}/class-teacher`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ class_teacher_id: classTeacherId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function registerFace(userId, imageBase64, lat, lon) {
  const res = await fetch(`${API_BASE}/register-face`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, image: imageBase64, latitude: lat, longitude: lon }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function trainModel() {
  const res = await fetch(`${API_BASE}/train`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function recognizeFace(imageBase64, lat, lon) {
  const res = await fetch(`${API_BASE}/recognize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: imageBase64, latitude: lat, longitude: lon }),
  });
  return res.json();
}

export async function markAttendance(userId, userName, type, lat, lon, locationOk) {
  const res = await fetch(`${API_BASE}/attendance/mark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      user_name: userName,
      type,
      latitude: lat,
      longitude: lon,
      location_ok: locationOk,
    }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function getAttendance(date, role, userId) {
  let url = `${API_BASE}/attendance?date=${date}`;
  if (role === 'class_teacher' && userId) url += `&role=class_teacher&user_id=${userId}`;
  const res = await fetch(url);
  const data = await res.json();
  return data.attendance || [];
}

export async function getAttendanceStats(role, userId, start, end) {
  let url = `${API_BASE}/attendance/stats?role=${role || ''}&user_id=${userId || ''}&start=${start}&end=${end}`;
  const res = await fetch(url);
  const data = await res.json();
  return data.stats || {};
}

export async function exportAttendance(role, userId, start, end, exportType = 'students') {
  let url = `${API_BASE}/export?role=${role}&user_id=${userId || 1}&start=${start}&end=${end}&export_type=${exportType}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Export failed');
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `attendance_${start}_to_${end}.xlsx`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export async function getCampus() {
  const res = await fetch(`${API_BASE}/campus`);
  const data = await res.json();
  return data.campus;
}

export async function setCampus(lat, lon, radius, name) {
  const res = await fetch(`${API_BASE}/campus`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ latitude: lat, longitude: lon, radius_meters: radius, name }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed');
  return data;
}

export async function getFaceRegistry() {
  const res = await fetch(`${API_BASE}/face-registry`);
  const data = await res.json();
  return data.registry || [];
}

export async function getStudentRecord(userId) {
  const res = await fetch(`${API_BASE}/students/${userId}/record`);
  if (!res.ok) throw new Error('Not found');
  return res.json();
}

export async function getStaffRecord(userId) {
  const res = await fetch(`${API_BASE}/staff/${userId}/record`);
  if (!res.ok) throw new Error('Not found');
  return res.json();
}
