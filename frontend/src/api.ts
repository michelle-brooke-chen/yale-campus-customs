export type StockStatus = 'in_stock' | 'low' | 'sold_out'

export interface ProductSummary {
  product_id: string
  name: string
  category: string
  description: string
  price: number
  image_url: string
  total_stock: number
}

export interface SizeStock {
  size: string
  quantity: number
  status: StockStatus
}

export interface Product extends ProductSummary {
  garment_type: string
  colors: string[]
  base_color: string
  inventory: SizeStock[]
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(res.status === 404 ? 'not_found' : `Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<ProductSummary[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatProduct {
  product_id: string
  name: string
  price: number
  image_url: string
}

export interface ChatReply {
  reply: string
  products: ChatProduct[]
}

export interface PageContext {
  path?: string
  product_id?: string
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: ChatProduct[]
}

export async function sendChat(
  message: string,
  history: ChatTurn[],
  pageContext?: PageContext,
): Promise<ChatReply> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page_context: pageContext ?? null }),
  })
  if (!res.ok) throw new Error(`Chat request failed (${res.status})`)
  return res.json() as Promise<ChatReply>
}

/** The signed-in shopper's saved conversation (empty for guests). */
export async function fetchChatHistory(): Promise<ChatHistoryMessage[]> {
  const res = await fetch('/api/chat/history')
  if (!res.ok) return []
  const data = (await res.json()) as { messages: ChatHistoryMessage[] }
  return data.messages
}

export const formatPrice = (price: number) =>
  price.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

// ---------- auth ----------
export interface User {
  id: number
  first_name: string | null
  last_name: string | null
  name: string
  email: string
  created_at: string
}

export interface SignupInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

/** Raised for handled auth failures; `message` is safe to show the user. */
export class AuthError extends Error {}

async function authRequest<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (res.ok) return res.json() as Promise<T>

  let detail = 'Something went wrong. Please try again.'
  try {
    const data = await res.json()
    if (typeof data.detail === 'string') detail = data.detail
    else if (Array.isArray(data.detail) && data.detail[0]?.msg) detail = data.detail[0].msg
  } catch {
    /* keep default */
  }
  throw new AuthError(detail)
}

export const apiSignup = (input: SignupInput) => authRequest<User>('/api/auth/signup', input)
export const apiLogin = (email: string, password: string) =>
  authRequest<User>('/api/auth/login', { email, password })

export async function apiLogout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST' })
}

export async function apiMe(): Promise<User | null> {
  const res = await fetch('/api/auth/me')
  return res.ok ? (res.json() as Promise<User>) : null
}
