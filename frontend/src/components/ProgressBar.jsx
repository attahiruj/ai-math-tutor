export default function ProgressBar({ value, color, label }) {
  return (
    <div style={{ width: '100%', marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <span style={{ fontSize: 15, fontWeight: 700, color: '#1E1A33' }}>{label}</span>
        <span style={{ fontSize: 15, fontWeight: 800, color }}>{Math.round(value * 100)}%</span>
      </div>
      <div style={{ height: 14, background: '#EDEAF8', borderRadius: 999, overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${value * 100}%`,
            background: color,
            borderRadius: 999,
            transition: 'width 0.8s ease',
          }}
        />
      </div>
    </div>
  )
}
