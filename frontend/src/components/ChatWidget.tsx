import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  fetchChatHistory,
  formatPrice,
  sendChat,
  type ChatProduct,
  type ChatTurn,
  type PageContext,
} from '../api'
import { useAuth } from '../auth-context'
import { useChatResults } from '../chat-results-context'
import ChatMarkdown from './ChatMarkdown'
import HandsomeDan from './HandsomeDan'

interface Message extends ChatTurn {
  id: number
  products?: ChatProduct[]
  error?: boolean
}

const GREETING: Message = {
  id: 0,
  role: 'assistant',
  content: 'Hi there, Bulldog! 👋 I can help you find Yale gear, check sizes, and see what’s in stock. What are you looking for?',
}

const SUGGESTIONS = ['What hoodies do you have?', 'Anything with Handsome Dan?', 'Cheapest fleece?']

let nextId = 1

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const { show } = useChatResults()
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  // Reload the conversation whenever the signed-in shopper changes. For signed-in
  // shoppers this restores their saved history; for guests the endpoint returns
  // nothing, so it resets to a clean greeting (e.g. after sign-out).
  useEffect(() => {
    let active = true
    fetchChatHistory()
      .then((hist) => {
        if (!active) return
        const restored: Message[] = hist.map((m) => ({
          id: nextId++,
          role: m.role,
          content: m.content,
          products: m.products,
        }))
        setMessages([GREETING, ...restored])
      })
      .catch(() => {
        if (active) setMessages([GREETING])
      })
    return () => {
      active = false
    }
  }, [user])

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages, sending, open])

  async function send(text: string) {
    const message = text.trim()
    if (!message || sending) return

    // History sent to the backend: every earlier real turn (not the greeting or errors).
    const history: ChatTurn[] = messages
      .filter((m) => m.id !== GREETING.id && !m.error)
      .map(({ role, content }) => ({ role, content }))

    // Tell the agent what page the shopper is on, so "this"/"it" resolves to the
    // product they're viewing.
    const productMatch = location.pathname.match(/^\/products\/(.+)$/)
    const pageContext: PageContext = {
      path: location.pathname,
      ...(productMatch ? { product_id: productMatch[1] } : {}),
    }

    setMessages((prev) => [...prev, { id: nextId++, role: 'user', content: message }])
    setInput('')
    setSending(true)
    try {
      const res = await sendChat(message, history, pageContext)
      setMessages((prev) => [
        ...prev,
        { id: nextId++, role: 'assistant', content: res.reply, products: res.products },
      ])
      // When the agent surfaced products, show them on the page's product panel
      // and bring the shopper to the Products page so they see the update. Stay put
      // if the only product is the one they're already viewing.
      if (res.products.length > 0) {
        show(message, res.products)
        const onlyCurrent =
          productMatch !== null && res.products.every((p) => p.product_id === productMatch[1])
        if (location.pathname !== '/products' && !onlyCurrent) navigate('/products')
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId++,
          role: 'assistant',
          content: 'Sorry, I couldn’t reach the shop assistant. Please try again in a moment.',
          error: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    send(input)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter adds a new line.
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send(input)
    }
  }

  return (
    <div className="chat" onKeyDown={(e) => e.key === 'Escape' && setOpen(false)}>
      {open && (
        <section id="chat-panel" className="chat-panel" role="dialog" aria-label="Shopping assistant chat">
          <header className="chat-header">
            <div className="chat-header-main">
              <span className="chat-avatar">
                <HandsomeDan size={34} pose="portrait" mood={sending ? 'thinking' : 'idle'} />
              </span>
              <div>
                <p className="chat-title">Bulldog Assistant</p>
                <p className="chat-subtitle">Ask about products, sizes, and stock</p>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>

          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`chat-msg chat-msg-${m.role}${m.error ? ' chat-msg-error' : ''}`}>
                {m.role === 'assistant' ? <ChatMarkdown text={m.content} /> : <p>{m.content}</p>}
                {m.products && m.products.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt="" />
                        <span className="chat-product-name">{p.name}</span>
                        <span className="chat-product-price">{formatPrice(p.price)}</span>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-msg chat-msg-assistant chat-typing" aria-label="Assistant is typing">
                <HandsomeDan size={26} mood="thinking" />
                <span /><span /><span />
              </div>
            )}
          </div>

          {messages.length === 1 && (
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          <form className="chat-input" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message…"
              rows={1}
              maxLength={2000}
              aria-label="Message"
            />
            <button type="submit" className="btn btn-primary" disabled={!input.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}

      <button
        className="chat-launcher"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="chat-panel"
        aria-label={open ? 'Close chat' : 'Open chat with the shopping assistant'}
      >
        {open ? '×' : <HandsomeDan size={40} />}
      </button>
    </div>
  )
}
