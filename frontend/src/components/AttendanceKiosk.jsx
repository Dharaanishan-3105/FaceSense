import { useState, useRef, useEffect, useCallback } from 'react'
import { recognizeFace, markAttendance } from '../api'

export default function AttendanceKiosk({ user }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('')
  const [location, setLocation] = useState({ lat: null, lon: null })
  const [capturing, setCapturing] = useState(false)

  const getLocation = useCallback(() => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => setStatus('Location not available')
    )
  }, [])

  useEffect(() => {
    getLocation()
  }, [getLocation])

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

  const captureFrame = () => {
    const v = videoRef.current
    const c = canvasRef.current
    if (!v || !c || !v.videoWidth) return null
    const ctx = c.getContext('2d')
    c.width = v.videoWidth
    c.height = v.videoHeight
    ctx.drawImage(v, 0, 0)
    return c.toDataURL('image/jpeg', 0.8)
  }

  const handleRecognize = async () => {
    const img = captureFrame()
    if (!img) return
    setCapturing(true)
    setStatus('Recognizing...')
    setResult(null)
    try {
      const data = await recognizeFace(img, location.lat, location.lon)
      setResult(data)
      if (data.recognized) {
        setStatus(data.location_ok ? 'Recognized - Press IN or OUT' : 'Location mismatch - attendance denied')
      } else {
        setStatus(data.message || 'Face not recognized')
      }
    } catch (err) {
      setStatus(err.message)
    } finally {
      setCapturing(false)
    }
  }

  const handleMark = async (type) => {
    if (!result?.recognized || !result.location_ok) return
    setCapturing(true)
    try {
      await markAttendance(result.user_id, result.name, type, location.lat, location.lon, true)
      setStatus(`${result.name} marked ${type.toUpperCase()} successfully`)
    } catch (err) {
      setStatus(err.message)
    } finally {
      setCapturing(false)
    }
  }

  return (
    <div className="card">
      <h2>Attendance Kiosk</h2>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Face pattern recognition with 80% accuracy. Location verified for campus presence.
      </p>

      <div className="video-container">
        <video ref={videoRef} autoPlay playsInline muted style={{ transform: 'scaleX(-1)' }} />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        <div className="video-overlay">
          FaceSense Pattern | {location.lat ? 'Location captured' : 'Requesting location...'}
        </div>
      </div>

      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleRecognize} disabled={capturing}>
          Recognize Face
        </button>
        {result?.recognized && result.location_ok && (
          <>
            <button className="btn btn-primary" onClick={() => handleMark('in')} disabled={capturing}>
              Mark IN
            </button>
            <button className="btn btn-primary" onClick={() => handleMark('out')} disabled={capturing}>
              Mark OUT
            </button>
          </>
        )}
      </div>

      {result && (
        <div className={`attendance-status ${result.recognized && result.location_ok ? 'success' : result.recognized ? 'error' : 'info'}`}>
          {result.recognized ? (
            <>
              <strong>{result.name}</strong> ({result.confidence}% match)
              {!result.location_ok && ' — Location verification failed'}
            </>
          ) : (
            status
          )}
        </div>
      )}
      {status && !result?.recognized && <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>{status}</p>}
    </div>
  )
}
