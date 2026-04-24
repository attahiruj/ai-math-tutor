import { useState, useEffect } from 'react'
import { LANGS } from '../i18n'
import Stars from './Stars'

export default function FeedbackScreen({ lang, correct, feedbackText, streak, onNext, onParent }) {
  const t = LANGS[lang]
  const [show, setShow] = useState(false)

  useEffect(() => {
    const id = setTimeout(() => setShow(true), 100)
    return () => clearTimeout(id)
  }, [])

  return (
    <div
      className="screen"
      style={{ background: correct ? 'oklch(95% 0.06 152)' : 'oklch(96% 0.05 30)', gap: 0 }}
      data-screen-label="04 Feedback"
    >
      <div
        style={{
          transform: show ? 'scale(1) translateY(0)' : 'scale(0.7) translateY(30px)',
          opacity: show ? 1 : 0,
          transition: 'all 0.45s cubic-bezier(0.34,1.56,0.64,1)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24,
        }}
      >
        <div
          style={{
            width: 120, height: 120, borderRadius: '50%',
            background: correct ? 'oklch(72% 0.14 152)' : 'oklch(72% 0.14 30)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 12px 40px ${correct ? 'oklch(72% 0.14 152)' : 'oklch(72% 0.14 30)'}66`,
            fontSize: 60,
          }}
        >
          {correct ? '✓' : '↺'}
        </div>

        <div style={{ fontSize: 46, fontWeight: 900, color: '#1E1A33' }}>
          {feedbackText || (correct ? t.correct : t.wrong)}
        </div>

        {correct && <Stars count={streak >= 3 ? 3 : streak >= 2 ? 2 : 1} />}

        {correct && (
          <div style={{ fontSize: 18, color: '#5A5480', fontWeight: 700, textAlign: 'center' }}>
            {streak > 1 ? `🔥 ${streak} in a row!` : t.keepGoing}
          </div>
        )}

        <div style={{ display: 'flex', gap: 16, marginTop: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
          <button className="btn-primary" onClick={onNext} style={{ fontSize: 22, padding: '18px 44px' }}>
            {t.next} →
          </button>
          <button className="btn-secondary" onClick={onParent}>{t.report}</button>
        </div>
      </div>
    </div>
  )
}
