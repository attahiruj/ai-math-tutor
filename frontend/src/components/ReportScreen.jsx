import { useState, useEffect } from 'react'
import { LANGS } from '../i18n'
import ProgressBar from './ProgressBar'

const DAY_LABELS = {
  EN:  ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
  FR:  ['L', 'M', 'M', 'J', 'V', 'S', 'D'],
  KIN: ['Mb', 'Ku', 'Ka', 'Ga', 'Ka', 'Ka', 'Ka'],
}

const SKILL_LABELS = {
  EN:  { counting: 'Counting', number_sense: 'Number Sense', addition: 'Addition', subtraction: 'Subtraction', word_problem: 'Word Problems' },
  FR:  { counting: 'Compter', number_sense: 'Sens des nombres', addition: 'Addition', subtraction: 'Soustraction', word_problem: 'Problèmes' },
  KIN: { counting: 'Kubara', number_sense: 'Kumva imibare', addition: 'Gukurikirana', subtraction: 'Gukuramo', word_problem: 'Ibibazo' },
}

const SKILL_ICONS = { counting: '🔢', number_sense: '🧮', addition: '➕', subtraction: '➖', word_problem: '📖' }

export default function ReportScreen({ lang, learner, onBack, api }) {
  const t = LANGS[lang]
  const [report, setReport] = useState(null)
  const [animIn, setAnimIn] = useState(false)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const data = await api.getReport(learner.student_id)
        setReport(data)
        setAnimIn(true)
      } catch (err) {
        console.error('Failed to fetch report:', err)
        setAnimIn(true)
      }
    }
    if (learner?.student_id) fetchReport()
    else setTimeout(() => setAnimIn(true), 50)
  }, [learner])

  const sessions = report?.attendance_7d || [0, 0, 0, 0, 0, 0, 0]
  const days = DAY_LABELS[lang] || DAY_LABELS.EN

  const skillLabels = SKILL_LABELS[lang] || SKILL_LABELS.EN

  const stats = [
    { icon: '⭐', val: `${report?.total_stars ?? 0}`,        label: 'Stars' },
    { icon: '📅', val: `${sessions.filter(Boolean).length}`, label: 'Days' },
    { icon: '📈', val: `${report?.overall_status || 'New'}`, label: 'Status' },
  ]

  return (
    <div
      className="screen"
      style={{ background: '#F4F1FF', overflowY: 'auto', justifyContent: 'flex-start', paddingTop: 28 }}
      data-screen-label="05 Parent Report"
    >
      <div
        style={{
          width: '100%', maxWidth: 560,
          opacity: animIn ? 1 : 0,
          transform: animIn ? 'translateY(0)' : 'translateY(20px)',
          transition: 'all 0.4s ease',
          display: 'flex', flexDirection: 'column', gap: 18,
        }}
      >
        {/* Header card */}
        <div className="card" style={{ background: learner?.color || 'oklch(68% 0.14 248)', padding: '24px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
            <div style={{
              width: 56, height: 56, borderRadius: '50%', background: 'rgba(255,255,255,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, fontWeight: 900, color: '#fff',
            }}>
              {learner?.avatar || 'A'}
            </div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 900, color: '#fff' }}>{learner?.name || 'Amara'}</div>
              <div style={{ fontSize: 15, color: 'rgba(255,255,255,0.75)', fontWeight: 600 }}>{t.parentTitle}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 20 }}>
            {stats.map((item) => (
              <div key={item.label} style={{ flex: 1, background: 'rgba(255,255,255,0.2)', borderRadius: 14, padding: '12px 8px', textAlign: 'center' }}>
                <div style={{ fontSize: 22 }}>{item.icon}</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: '#fff' }}>{item.val}</div>
                <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.75)', fontWeight: 600 }}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly attendance */}
        <div className="card">
          <div style={{ fontSize: 17, fontWeight: 800, color: '#1E1A33', marginBottom: 16 }}>📅 {t.parentSub}</div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'space-between' }}>
            {sessions.map((active, i) => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                <div style={{
                  width: '100%', aspectRatio: '1', borderRadius: 12,
                  background: active ? 'oklch(72% 0.14 152)' : '#EDEAF8',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18,
                }}>
                  {active ? '✓' : ''}
                </div>
                <div style={{ fontSize: 13, color: '#8A85A5', fontWeight: 700 }}>{days[i]}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Skills */}
        <div className="card">
          <div style={{ fontSize: 17, fontWeight: 800, color: '#1E1A33', marginBottom: 18 }}>📊 {t.skills}</div>
          {report
            ? Object.entries(report.skills || {}).map(([key, data]) => {
                const mastery = typeof data === 'object' && data !== null
                  ? (data.mastery ?? data.current ?? data.p_mastery ?? 0)
                  : 0
                const label = skillLabels[key] || key.replace(/_/g, ' ')
                const icon = SKILL_ICONS[key] || '📚'
                return (
                  <ProgressBar
                    key={key}
                    label={`${icon} ${label}`}
                    value={animIn ? mastery : 0}
                    color={mastery > 0.7 ? 'oklch(72% 0.14 152)' : mastery > 0.4 ? 'oklch(84% 0.14 88)' : 'oklch(72% 0.14 30)'}
                  />
                )
              })
            : <div style={{ color: '#8A85A5' }}>Loading skills...</div>
          }
        </div>

        <button className="btn-secondary" onClick={onBack} style={{ alignSelf: 'center', marginBottom: 12 }}>
          ← Back
        </button>
      </div>
    </div>
  )
}
