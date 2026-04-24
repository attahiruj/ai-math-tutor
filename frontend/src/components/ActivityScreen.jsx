import { useState, useEffect, useMemo } from 'react'
import { LANGS } from '../i18n'
import { ShapeIcon } from '../utils/emoji'

const COLORS = {
  blue:   'oklch(68% 0.14 248)',
  green:  'oklch(72% 0.14 152)',
  yellow: 'oklch(84% 0.14 88)',
  coral:  'oklch(72% 0.14 30)',
  purple: 'oklch(68% 0.14 295)',
  teal:   'oklch(70% 0.14 196)',
}

// Max shapes to render before switching to numeric display
const MAX_SHAPES = 15

function placeItems(count, shape, xStart, yStart, xEnd, yEnd, startDelay, dimmed = false) {
  if (count <= 0) return []
  const width = Math.max(1, xEnd - xStart)
  const height = Math.max(1, yEnd - yStart)
  const cols = Math.max(1, Math.ceil(Math.sqrt(count * (width / height))))
  const rows = Math.ceil(count / cols)
  const cellW = width / cols
  const cellH = height / rows
  return Array.from({ length: count }, (_, i) => ({
    x: xStart + (i % cols) * cellW + cellW / 2 - 25 + (Math.random() * 10 - 5),
    y: yStart + Math.floor(i / cols) * cellH + cellH / 2 - 25 + (Math.random() * 8 - 4),
    delay: startDelay + i * 60,
    shape,
    dimmed,
  }))
}

function NumberExpr({ meta }) {
  const numStyle = { fontSize: 60, fontWeight: 900, color: '#1E1A33', lineHeight: 1 }
  const opStyle  = { fontSize: 40, fontWeight: 900, lineHeight: 1 }
  const eqStyle  = { fontSize: 40, fontWeight: 700, color: '#B0ABCC', lineHeight: 1 }

  const wrap = (children) => (
    <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', gap: 20 }}>
      {children}
    </div>
  )

  if (!meta) return null

  if (meta.type === 'addition') return wrap(<>
    <span style={numStyle}>{meta.a}</span>
    <span style={{ ...opStyle, color: COLORS.green }}>+</span>
    <span style={numStyle}>{meta.b}</span>
    <span style={eqStyle}>=</span>
    <span style={{ ...numStyle, color: '#B0ABCC' }}>?</span>
  </>)

  if (meta.type === 'subtraction') return wrap(<>
    <span style={numStyle}>{meta.a}</span>
    <span style={{ ...opStyle, color: COLORS.coral }}>−</span>
    <span style={numStyle}>{meta.b}</span>
    <span style={eqStyle}>=</span>
    <span style={{ ...numStyle, color: '#B0ABCC' }}>?</span>
  </>)

  if (meta.type === 'counting') return wrap(
    <span style={{ fontSize: 80, fontWeight: 900, color: '#1E1A33' }}>{meta.count}</span>
  )

  if (meta.type === 'word_problem') return wrap(<>
    <span style={numStyle}>{meta.n1}</span>
    <span style={eqStyle}>·</span>
    <span style={numStyle}>{meta.n2}</span>
  </>)

  return null
}

export default function ActivityScreen({ lang, learner, item, onAnswer, questionIdx, silenceCountdown, api }) {
  const t = LANGS[lang]
  const [selected, setSelected] = useState(null)
  const [animObjs, setAnimObjs] = useState([])
  const [visualMode, setVisualMode] = useState('image')

  useEffect(() => {
    setSelected(null)
    let meta = item.visual_meta

    // Back-compat: old server returns {shape, count, layout} without a type field.
    // The old rsplit parser broke compound visuals (e.g. "beans_9_minus_2" → count=2),
    // so only trust the old count when the shape name contains no math keyword.
    if (meta && !meta.type) {
      const shapeName = meta.shape ?? ''
      const looksCompound = /minus|plus|basket|market|tank/.test(shapeName)
      if (meta.count > 0 && !looksCompound) {
        meta = { type: 'counting', shape: shapeName, count: meta.count, layout: meta.layout ?? 'scatter' }
      } else {
        // Old server can't give us reliable data for this visual — fall to number mode
        // if we can extract a and b from the raw visual string, otherwise hide.
        const raw = item.visual ?? ''
        const mPlus  = raw.match(/(\d+)_plus_(\d+)/)
        const mMinus = raw.match(/(\d+)_minus_(\d+)/)
        if (mPlus)  meta = { type: 'addition',    shape: '', a: +mPlus[1],  b: +mPlus[2]  }
        else if (mMinus) meta = { type: 'subtraction', shape: '', a: +mMinus[1], b: +mMinus[2] }
        else        meta = null
      }
    }

    if (!meta || meta.type === 'static') {
      setAnimObjs([])
      setVisualMode('image')
      return
    }

    if (meta.type === 'comparison') {
      setAnimObjs([])
      setVisualMode('comparison')
      return
    }

    if (meta.type === 'counting') {
      const { shape, count, layout } = meta
      if (count <= 0) { setAnimObjs([]); setVisualMode('image'); return }
      if (count > MAX_SHAPES) { setAnimObjs([]); setVisualMode('number'); return }
      let positions
      if (layout === 'row') {
        const step = Math.min(58, 440 / count)
        positions = Array.from({ length: count }, (_, i) => ({
          x: 30 + i * step, y: 80, delay: i * 60, shape, dimmed: false,
        }))
      } else {
        positions = placeItems(count, shape, 30, 20, 470, 170, 0)
      }
      setAnimObjs(positions)
      setVisualMode('shapes')
      return
    }

    if (meta.type === 'addition') {
      const { shape, a, b } = meta
      if (a > MAX_SHAPES || b > MAX_SHAPES || a + b > MAX_SHAPES + 5) {
        setAnimObjs([]); setVisualMode('number'); return
      }
      const leftObjs  = placeItems(a, shape, 15,  30, 215, 180, 0)
      const rightObjs = placeItems(b, shape, 270, 30, 480, 180, a * 60)
      setAnimObjs([...leftObjs, ...rightObjs])
      setVisualMode('addition')
      return
    }

    if (meta.type === 'subtraction') {
      const { shape, a, b } = meta
      if (a > MAX_SHAPES) { setAnimObjs([]); setVisualMode('number'); return }
      const positions = placeItems(a, shape, 30, 20, 470, 170, 0)
      for (let i = a - b; i < a; i++) positions[i].dimmed = true
      setAnimObjs(positions)
      setVisualMode('subtraction')
      return
    }

    if (meta.type === 'word_problem') {
      const { shape1, n1, shape2, n2 } = meta
      if (n1 > MAX_SHAPES || n2 > MAX_SHAPES || n1 + n2 > MAX_SHAPES + 5) {
        setAnimObjs([]); setVisualMode('number'); return
      }
      const leftObjs  = placeItems(n1, shape1, 15,  30, 220, 180, 0)
      const rightObjs = placeItems(n2, shape2, 260, 30, 480, 180, n1 * 60)
      setAnimObjs([...leftObjs, ...rightObjs])
      setVisualMode('word_problem')
      return
    }

    setAnimObjs([])
    setVisualMode('image')
  }, [item.id])

  const choices = useMemo(
    () => [...item.distractors, item.answer_int].sort(() => Math.random() - 0.5),
    [item.id]
  )

  const handleSelect = (val) => {
    if (selected !== null) return
    setSelected(val)
    setTimeout(() => onAnswer(val), 700)
  }

  const canvasH = 210
  const stem = item[`stem_${lang.toLowerCase()}`] || item.stem_en
  const showCanvas = visualMode === 'comparison' || visualMode === 'number' || animObjs.length > 0

  return (
    <div
      className="screen"
      style={{ background: '#F4F1FF', gap: 0, padding: '20px 24px' }}
      data-screen-label="03 Counting Activity"
    >
      {/* Top bar */}
      <div style={{ width: '100%', maxWidth: 560, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <div style={{
            width: 42, height: 42, borderRadius: '50%', background: learner?.color || COLORS.blue,
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 900, fontSize: 18,
          }}>
            {learner?.avatar || 'A'}
          </div>
          <div style={{ fontWeight: 800, fontSize: 16, color: '#1E1A33' }}>{learner?.name || 'Learner'}</div>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{
              width: 12, height: 12, borderRadius: '50%',
              background: i < questionIdx ? COLORS.green : i === questionIdx ? COLORS.blue : '#DDD8F5',
            }} />
          ))}
        </div>

        {silenceCountdown < 8 && (
          <div style={{ fontSize: 14, color: COLORS.coral, fontWeight: 800 }}>⏱ {silenceCountdown}s</div>
        )}
      </div>

      {/* Question card */}
      <div className="card" style={{ width: '100%', maxWidth: 560, marginBottom: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 22, fontWeight: 700, color: '#8A85A5', marginBottom: 8 }}>{stem}</div>

        {showCanvas && (
          <div style={{
            position: 'relative', height: canvasH, width: '100%', background: 'oklch(96% 0.03 248)',
            borderRadius: 16, overflow: 'hidden', margin: '0 auto',
          }}>
            {visualMode === 'comparison' ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'space-around', padding: '0 30px' }}>
                <div style={{ fontSize: 80, fontWeight: 900, color: '#1E1A33' }}>{item.visual_meta.a}</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: '#B0ABCC' }}>vs</div>
                <div style={{ fontSize: 80, fontWeight: 900, color: '#1E1A33' }}>{item.visual_meta.b}</div>
              </div>
            ) : visualMode === 'number' ? (
              <NumberExpr meta={item.visual_meta} />
            ) : (
              <>
                {animObjs.map((pos, i) => (
                  <div
                    key={i}
                    style={{
                      position: 'absolute', left: pos.x, top: pos.y,
                      opacity: pos.dimmed ? 0.28 : (selected !== null ? 0.7 : 1),
                      animation: `popIn 0.35s ${pos.delay}ms both ease-out`,
                      filter: pos.dimmed ? 'grayscale(1)' : 'none',
                    }}
                  >
                    <ShapeIcon shape={pos.shape} color={COLORS.blue} size={50} />
                  </div>
                ))}
                {visualMode === 'addition' && (
                  <div style={{
                    position: 'absolute', left: 221, top: 80,
                    fontSize: 40, fontWeight: 900, color: COLORS.green,
                    lineHeight: '50px', width: 48, textAlign: 'center',
                    pointerEvents: 'none',
                  }}>+</div>
                )}
                {visualMode === 'subtraction' && (
                  <div style={{
                    position: 'absolute', bottom: 8, right: 12,
                    fontSize: 11, fontWeight: 700, color: COLORS.coral,
                    pointerEvents: 'none',
                  }}>faded = taken away</div>
                )}
              </>
            )}
          </div>
        )}

        <div style={{ fontSize: 15, color: '#B0ABCC', fontWeight: 600, marginTop: 12 }}>{t.tap}</div>
      </div>

      {/* Answer choices */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, width: '100%', maxWidth: 560 }}>
        {choices.map((val) => {
          const isCorrect = val === item.answer_int
          let bg = '#fff', border = '#E0DCF5'
          if (selected !== null) {
            if (val === selected && isCorrect)  { bg = 'oklch(72% 0.14 152)'; border = COLORS.green }
            else if (val === selected)          { bg = 'oklch(85% 0.10 30)';  border = COLORS.coral }
            else if (isCorrect)                 { bg = 'oklch(72% 0.14 152)'; border = COLORS.green }
          }
          const highlighted = selected !== null && (val === selected || val === item.answer_int)
          return (
            <button
              key={val}
              onClick={() => handleSelect(val)}
              style={{
                padding: '18px 12px', borderRadius: 18,
                border: `3px solid ${highlighted ? border : '#E0DCF5'}`,
                background: bg,
                fontFamily: 'Nunito', fontSize: 36, fontWeight: 900,
                color: highlighted ? '#fff' : '#1E1A33',
                cursor: selected === null ? 'pointer' : 'default',
                boxShadow: '0 4px 16px rgba(60,40,120,0.08)',
                transform: selected === val ? 'scale(0.97)' : 'scale(1)',
                transition: 'all 0.2s ease',
              }}
            >
              {val}
            </button>
          )
        })}
      </div>
    </div>
  )
}
