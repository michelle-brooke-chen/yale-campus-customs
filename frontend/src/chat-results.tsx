import { useState, type ReactNode } from 'react'
import type { ChatProduct } from './api'
import { ChatResultsContext } from './chat-results-context'

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatProduct[]>([])
  const [query, setQuery] = useState<string | null>(null)

  const value = {
    results,
    query,
    show: (q: string, items: ChatProduct[]) => {
      setQuery(q)
      setResults(items)
    },
    clear: () => {
      setQuery(null)
      setResults([])
    },
  }

  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}
