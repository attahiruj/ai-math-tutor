import { useState, useEffect } from 'react'
import { LANGS } from '../i18n'

export default function WelcomeScreen({ lang, setLang, onNext }) {
  const t = LANGS[lang]
  const [pulse, setPulse] = useState(false)

  useEffect(() => {
    const id = setInterval(() => setPulse((p) => !p), 1800)
    return () => clearInterval(id)
  }, [])

  return (
    <div
      className="screen"
      style={{ background: 'linear-gradient(160deg, #F4F1FF 0%, #EBF5FF 100%)', gap: 0 }}
      data-screen-label="01 Welcome"
    >
      <div
        style={{
          width: 110, height: 110, borderRadius: '50%', background: 'white',
          boxShadow: '0 8px 32px rgba(100,80,200,0.18)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 28,
          transform: pulse ? 'scale(1.04)' : 'scale(1)', transition: 'transform 0.8s ease',
        }}
      >
        <svg width={60} height={60} viewBox="0 0 60 60">
          <circle cx={30} cy={30} r={28} fill="oklch(68% 0.14 248)" opacity={0.15} />
          <text x={30} y={38} textAnchor="middle" fontSize={32} fontFamily="Nunito" fontWeight={900} fill="oklch(55% 0.18 248)">
            1+2
          </text>
        </svg>
      </div>

      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ fontSize: 52, fontWeight: 900, color: '#1E1A33', lineHeight: 1.1, letterSpacing: -1 }}>
          MathKids
        </div>
        <div style={{ fontSize: 20, fontWeight: 600, color: '#8A85A5', marginTop: 8 }}>
          {t.welcome} — {t.sub}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 40 }}>
        {Object.values(LANGS).map((l) => (
          <button
            key={l.code}
            onClick={() => setLang(l.code)}
            style={{
              padding: '10px 20px', borderRadius: 999,
              border: lang === l.code ? '3px solid oklch(68% 0.14 248)' : '3px solid #E0DCF5',
              background: lang === l.code ? 'oklch(68% 0.14 248)' : '#fff',
              color: lang === l.code ? '#fff' : '#1E1A33',
              fontFamily: 'Nunito', fontSize: 16, fontWeight: 800, cursor: 'pointer', transition: 'all 0.2s',
            }}
          >
            {l.flag} {l.code}
          </button>
        ))}
      </div>

      <button className="btn-primary" onClick={onNext} style={{ fontSize: 26, padding: '20px 64px' }}>
        {t.start}
      </button>

      <div style={{ position: 'absolute', bottom: 24, fontSize: 14, color: '#B0ABCC', fontWeight: 600 }}>
        Tap · Touch · Voice — works offline
      </div>
    </div>
  )
}
