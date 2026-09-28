import { createContext, useContext } from 'react'
import type { ChatProduct } from './api'

export interface ChatResultsValue {
  /** Products the agent surfaced in the latest chat turn (drives the page panel). */
  results: ChatProduct[]
  /** The shopper's question that produced them, for a friendly panel heading. */
  query: string | null
  show: (query: string, results: ChatProduct[]) => void
  clear: () => void
}

export const ChatResultsContext = createContext<ChatResultsValue | null>(null)

export function useChatResults() {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
