export class AudioRecorder {
  constructor() {
    this.mediaRecorder = null
    this.audioChunks = []
    this.stream = null
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    this.mediaRecorder = new MediaRecorder(this.stream)
    this.audioChunks = []
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.audioChunks.push(event.data)
    }
    this.mediaRecorder.start()
  }

  stop() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No recording in progress'))
        return
      }
      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
        if (this.stream) {
          this.stream.getTracks().forEach((t) => t.stop())
          this.stream = null
        }
        resolve(audioBlob)
      }
      this.mediaRecorder.stop()
    })
  }

  isRecording() {
    return this.mediaRecorder && this.mediaRecorder.state === 'recording'
  }
}
