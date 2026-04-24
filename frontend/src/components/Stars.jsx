export default function Stars({ count, max = 3 }) {
  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
      {Array.from({ length: max }, (_, i) => (
        <svg
          key={i}
          width={44}
          height={44}
          viewBox="0 0 54 54"
          style={{ filter: i < count ? 'drop-shadow(0 2px 6px rgba(245,200,80,0.5))' : 'none' }}
        >
          <polygon
            points="27,4 33,20 51,20 37,31 42,48 27,38 12,48 17,31 3,20 21,20"
            fill={i < count ? 'oklch(84% 0.18 88)' : '#E5E0F5'}
          />
        </svg>
      ))}
    </div>
  )
}
