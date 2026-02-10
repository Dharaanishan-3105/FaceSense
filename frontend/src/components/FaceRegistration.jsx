import { useState, useRef, useEffect } from 'react'
import { registerFace } from '../api'

const TARGET_SAMPLES = 30

export default function FaceRegistration({ user, onDone }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [count, setCount] = useState(0)
  const [status, setStatus] = useState('')
  const [location, setLocation] = useState({ lat: null, lon: null })

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (p) => setLocation({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => setStatus('Allow location for first-time registration')
    )
  }, [])

  useEffect(() => {
    let s
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
      .then((str) => {
        s = str
        setStream(str)
        if (videoRef.current) videoRef.current.srcObject = str
      })
      .catch(() => setStatus('Camera access denied'))
    return () => { if (s) s.getTracks().forEach((t) => t.stop()) }
  }, [])

  const captureAndSend = async () => {
    const v = videoRef.current
    const c = canvasRef.current
    if (!v || !c || !v.videoWidth) return
    const ctx = c.getContext('2d')
    c.width = v.videoWidth
    c.height = v.videoHeight
    ctx.drawImage(v, 0, 0)
    const img = c.toDataURL('image/jpeg', 0.8)
    try {
      await registerFace(user.id, img, location.lat, location.lon)
      setCount((prev) => prev + 1)
      setStatus(`Captured ${count + 1}/${TARGET_SAMPLES}`)
    } catch (e) {
      setStatus(e.message)
    }
  }

  return (
    <div className="card">
      <h2>Register Face &amp; Location - {user.name}</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
        First-time registration captures your face pattern and location. Collect {TARGET_SAMPLES} samples.
      </p>

      <div className="video-container">
        <video ref={videoRef} autoPlay playsInline muted style={{ transform: 'scaleX(-1)' }} />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        <div className="video-overlay">
          FaceSense Pattern | {count}/{TARGET_SAMPLES} samples | {location.lat ? 'Location ready' : 'Getting location...'}
        </div>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <button className="btn btn-primary" onClick={captureAndSend} disabled={count >= TARGET_SAMPLES}>
          Capture sample ({count}/{TARGET_SAMPLES})
        </button>
        <button className="btn" onClick={onDone} style={{ marginLeft: '0.5rem' }}>Done</button>
      </div>
      {status && <p style={{ marginTop: '0.5rem', color: 'var(--accent)' }}>{status}</p>}
    </div>
  )
}
