export const EMOJIS = {
  apples: '🍎', goats: '🐐', stars: '⭐', fish: '🐟', fingers: '☝️',
  mangoes: '🥭', cows: '🐄', water: '💧', mandazi: '🍩',
  beads: '📿', bananas: '🍌', drums: '🥁', beans: '🫘',
  tomatoes: '🍅', birds: '🐦', seeds: '🌱', pupils: '🧒',
  oranges: '🍊', frogs: '🐸', balls: '⚽', eggs: '🥚',
  chairs: '🪑', cookies: '🍪',
}

export function ShapeIcon({ shape, color, size = 54 }) {
  const emoji = EMOJIS[shape] || EMOJIS[shape + 's']
  if (emoji) {
    return (
      <div style={{ fontSize: size * 0.9, width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {emoji}
      </div>
    )
  }
  if (shape === 'star') {
    return (
      <svg width={size} height={size} viewBox="0 0 54 54">
        <polygon
          points="27,4 33,20 51,20 37,31 42,48 27,38 12,48 17,31 3,20 21,20"
          fill={color}
          stroke="rgba(0,0,0,0.08)"
          strokeWidth="1.5"
        />
      </svg>
    )
  }
  return (
    <svg width={size} height={size} viewBox="0 0 54 54">
      <circle cx="27" cy="27" r="22" fill={color} stroke="rgba(0,0,0,0.08)" strokeWidth="1.5" />
    </svg>
  )
}
