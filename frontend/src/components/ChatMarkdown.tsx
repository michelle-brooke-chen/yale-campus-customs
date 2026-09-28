import type { ReactNode } from 'react'

/**
 * Render the small Markdown subset the agent uses: paragraphs, bullet and
 * numbered lists, **bold**, *italic*, and `code`. Builds React elements
 * directly (no raw HTML), so reply text can never inject markup.
 */

const INLINE = /(\*\*[^*]+\*\*|__[^_]+__|\*[^*\s][^*]*\*|_[^_\s][^_]*_|`[^`]+`|\[[^\]]+\]\([^)]+\))/g
const BULLET = /^\s*[-*•]\s+/
const NUMBERED = /^\s*\d+[.)]\s+/

function renderInline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (/^(\*\*|__).+\1$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>
    if (/^`.+`$/.test(part)) return <code key={i}>{part.slice(1, -1)}</code>
    if (/^([*_]).+\1$/.test(part)) return <em key={i}>{part.slice(1, -1)}</em>
    // Links show their label only; product links arrive as cards instead.
    const link = part.match(/^\[([^\]]+)\]\([^)]+\)$/)
    if (link) return link[1]
    return part
  })
}

/** Paragraph text with single line breaks kept. */
function renderLines(lines: string[]): ReactNode[] {
  return lines.flatMap((line, i) => (i === 0 ? renderInline(line) : [<br key={`br${i}`} />, ...renderInline(line)]))
}

export default function ChatMarkdown({ text }: { text: string }) {
  const blocks: ReactNode[] = []
  let para: string[] = []
  let list: { ordered: boolean; items: string[] } | null = null

  const flushPara = () => {
    if (para.length) blocks.push(<p key={blocks.length}>{renderLines(para)}</p>)
    para = []
  }
  const flushList = () => {
    if (list) {
      const items = list.items.map((item, i) => <li key={i}>{renderInline(item)}</li>)
      blocks.push(list.ordered ? <ol key={blocks.length}>{items}</ol> : <ul key={blocks.length}>{items}</ul>)
    }
    list = null
  }

  for (const raw of text.split('\n')) {
    const line = raw.trimEnd()
    const ordered = NUMBERED.test(line)
    if (ordered || BULLET.test(line)) {
      flushPara()
      if (list && list.ordered !== ordered) flushList()
      list ??= { ordered, items: [] }
      list.items.push(line.replace(ordered ? NUMBERED : BULLET, ''))
    } else if (!line.trim()) {
      flushPara()
      flushList()
    } else {
      flushList()
      // Treat "# Heading" lines as bold paragraphs.
      para.push(line.replace(/^#{1,6}\s+(.*)$/, '**$1**'))
    }
  }
  flushPara()
  flushList()

  return <div className="chat-md">{blocks}</div>
}
