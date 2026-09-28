import { useEffect, useRef, type ReactElement } from 'react'

/**
 * Handsome Dan, drawn as pixel art. Each character in a sprite is one pixel;
 * "." is transparent. Rows above HEAD_ROWS form the head, which animates
 * separately from the sweater so he can bob, blink, and pant.
 */
const SITTING = [
  '..ooo........ooo..',
  '.otttoooooooottto.',
  'otttwwwwwwwwwwttto',
  'owttttwwwwwwwwwwwo',
  'owteewwwwwwwweewwo',
  'owteewwwwwwwweewwo',
  'owbwwwwkkkkwwwwbwo',
  'owwwwwwwkkwwwwwwwo',
  'otwwwkkfkkfkkwwwto',
  'ottwwwkkppkkwwwtto',
  '.ottwwwwkkwwwwtto.',
  '..oooooooooooooo..',
  '.onnnnnnnnnnnnnno.',
  '.onnnnnynnynnnnno.',
  '.onnnnnnyynnnnnno.',
  '.onnnnnnyynnnnnno.',
  '.orrrrrrrrrrrrrro.',
  '.owwwo......owwwo.',
  '..ooo........ooo..',
]

// Close-up for the chat avatar: a wink and a happy tongue, cropped at the collar.
const PORTRAIT = [
  '..ooo........ooo..',
  '.otttoooooooottto.',
  'otttwwwwwwwwwwttto',
  'owttttwwwwwwwwwwwo',
  'owteewwwwwwwwkkwwo',
  'owteewwwwwwwkwwkwo',
  'owbwwwwkkkkwwwwbwo',
  'owwwwwwwkkwwwwwwwo',
  'otwwwkkfkkfkkwwwto',
  'ottwwwkkppkkwwwtto',
  '.ottwwwwppwwwwtto.',
  '..ooooooppoooooo..',
  '.onnnnnnnnnnnnnno.',
  '.orrrrrrrrrrrrrro.',
]

const HEAD_ROWS = 12

// Side view for the runner, facing right. Two leg frames alternate as he runs.
const RUNNER = [
  '........ooo.....',
  '.......ottoooo..',
  '......owwwwwwwo.',
  'o.....owwwwewwwo',
  '.ooooowwwwwwwkko',
  'onnnnnowwwbwwwwo',
  'onnnnnnottwwkfko',
  'onnnnnnnottwwpo.',
  'onnnnnnnnoooooo.',
  'orrrrrrrrro.....',
]
const RUNNER_STRIDE = ['owo.....owo.....', 'oo.......oo.....']
const RUNNER_TUCK = ['..owo.owo.......', '...oo..oo.......']

const COLORS: Record<string, string> = {
  o: '#10233a', // outline
  w: '#fffdf8', // fur
  t: '#e8c39e', // tan patches
  e: '#10233a', // eyes
  k: '#10233a', // nose and mouth
  f: '#ffffff', // underbite fangs
  b: '#f9c2cf', // blush
  p: '#f28aa5', // tongue
  n: '#1f4e85', // sweater
  r: '#173d69', // sweater ribbing
  y: '#ffffff', // sweater Y
}

// Pixels that belong to an animated part rather than the base layer.
const PART: Record<string, 'eyes' | 'tongue'> = { e: 'eyes', p: 'tongue' }

type Layer = 'base' | 'eyes' | 'tongue'

/** Merge each row into horizontal runs of one color, grouped by layer. */
function buildRects(rows: string[], offset = 0) {
  const layers: Record<Layer, ReactElement[]> = { base: [], eyes: [], tongue: [] }
  rows.forEach((row, i) => {
    const y = i + offset
    let x = 0
    while (x < row.length) {
      const ch = row[x]
      let end = x + 1
      while (end < row.length && row[end] === ch) end++
      if (ch !== '.') {
        const rect = (fill: string) => (
          <rect key={`${x}-${y}`} x={x} y={y} width={end - x} height={1} fill={fill} />
        )
        const part = PART[ch]
        // Animated parts get fur underneath so blinking or panting never leaves a hole.
        if (part) layers.base.push(rect(COLORS.w))
        layers[part ?? 'base'].push(rect(COLORS[ch]))
      }
      x = end
    }
  })
  return layers
}

function splitPose(rows: string[]) {
  return {
    rows,
    head: buildRects(rows.slice(0, HEAD_ROWS)),
    body: buildRects(rows.slice(HEAD_ROWS), HEAD_ROWS),
  }
}

const POSES = { sitting: splitPose(SITTING), portrait: splitPose(PORTRAIT) }

const runner = buildRects(RUNNER)
const stride = buildRects(RUNNER_STRIDE, RUNNER.length)
const tuck = buildRects(RUNNER_TUCK, RUNNER.length)
const RUNNER_HEIGHT = RUNNER.length + RUNNER_STRIDE.length

interface SpriteSvgProps {
  width: number
  height: number
  size: number
  className: string
  label?: string
  children: ReactElement | ReactElement[]
}

function SpriteSvg({ width, height, size, className, label, children }: SpriteSvgProps) {
  return (
    <svg
      className={className}
      width={size}
      height={(size * height) / width}
      viewBox={`0 0 ${width} ${height}`}
      shapeRendering="crispEdges"
      role={label ? 'img' : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      {children}
    </svg>
  )
}

interface HandsomeDanProps {
  size?: number
  pose?: keyof typeof POSES
  mood?: 'idle' | 'thinking'
  className?: string
  label?: string
}

export default function HandsomeDan({
  size = 64,
  pose = 'sitting',
  mood = 'idle',
  className = '',
  label,
}: HandsomeDanProps) {
  const { rows, head, body } = POSES[pose]
  return (
    <SpriteSvg
      width={rows[0].length}
      height={rows.length}
      size={size}
      className={`dan dan-${pose} dan-${mood} ${className}`.trim()}
      label={label}
    >
      <g className="dan-body">{body.base}</g>
      <g className="dan-head">
        {head.base}
        <g className="dan-eyes">{head.eyes}</g>
        <g className="dan-tongue">{head.tongue}</g>
      </g>
    </SpriteSvg>
  )
}

// How close (in px) the cursor must come before the runner hops.
const HOP_RADIUS = 80
// Matches the dan-startle animation length in index.css.
const HOP_MS = 450

/** A tiny Dan who runs back and forth, and hops when the cursor comes near. */
export function DanRunner({ size = 30 }: { size?: number }) {
  const hopperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const hopper = hopperRef.current
    if (!hopper) return
    let frame = 0
    let pointer: { x: number; y: number } | null = null
    let landing = 0

    function check() {
      frame = 0
      if (!hopper || !pointer || hopper.classList.contains('dan-hopping')) return
      const { x, y } = pointer
      const r = hopper.getBoundingClientRect()
      const dx = x - (r.left + r.width / 2)
      const dy = y - (r.top + r.height / 2)
      if (dx * dx + dy * dy < HOP_RADIUS * HOP_RADIUS) {
        hopper.classList.add('dan-hopping')
        landing = window.setTimeout(() => hopper.classList.remove('dan-hopping'), HOP_MS)
      }
    }

    function onMove(e: PointerEvent) {
      pointer = { x: e.clientX, y: e.clientY }
      if (!frame) frame = requestAnimationFrame(check)
    }

    // Also re-check while the cursor rests, so he hops if he runs into it.
    const timer = window.setInterval(check, 150)

    window.addEventListener('pointermove', onMove)
    return () => {
      window.removeEventListener('pointermove', onMove)
      cancelAnimationFrame(frame)
      window.clearInterval(timer)
      window.clearTimeout(landing)
    }
  }, [])

  return (
    <div className="dan-track" aria-hidden="true">
      <div className="dan-runner">
        <div className="dan-hopper" ref={hopperRef}>
          <SpriteSvg width={RUNNER[0].length} height={RUNNER_HEIGHT} size={size} className="dan dan-run">
            <g>{runner.base}</g>
            <g className="dan-legs-stride">{stride.base}</g>
            <g className="dan-legs-tuck">{tuck.base}</g>
          </SpriteSvg>
        </div>
      </div>
    </div>
  )
}
