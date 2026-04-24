const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export class APIClient {
  constructor(baseUrl = API_BASE) {
    this.baseUrl = baseUrl
  }

  async startSession(name, lang, icon) {
    const res = await fetch(`${this.baseUrl}/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, lang, icon }),
    })
    return res.json()
  }

  async endSession(sessionId) {
    const res = await fetch(`${this.baseUrl}/session/end`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    })
    return res.json()
  }

  async getNextItem(studentId, lang) {
    const res = await fetch(`${this.baseUrl}/item/next?student_id=${studentId}&lang=${lang}`)
    return res.json()
  }

  async submitTap(studentId, sessionId, itemId, choice) {
    const res = await fetch(`${this.baseUrl}/answer/tap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        session_id: sessionId,
        item_id: itemId,
        choice,
      }),
    })
    return res.json()
  }

  async submitVoice(studentId, sessionId, itemId, audioBlob, lang) {
    const formData = new FormData()
    formData.append('student_id', studentId)
    formData.append('session_id', sessionId)
    formData.append('item_id', itemId)
    formData.append('lang', lang)
    formData.append('audio', audioBlob)
    const res = await fetch(`${this.baseUrl}/answer/voice`, { method: 'POST', body: formData })
    return res.json()
  }

  async getReport(studentId) {
    const res = await fetch(`${this.baseUrl}/report/${studentId}`)
    return res.json()
  }

  getImageUrl(visualRef) {
    return `${this.baseUrl}/images/${visualRef}.png`
  }

  getTTSUrl(lang, itemId) {
    return `${this.baseUrl}/tts/${lang}/${itemId}`
  }
}
