import { useEffect, useState, type ReactNode } from 'react'
import { apiLogin, apiLogout, apiMe, apiSignup, type SignupInput, type User } from './api'
import { AuthContext, type AuthContextValue } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Restore the session (if any) from the cookie on first load.
    apiMe()
      .then(setUser)
      .finally(() => setLoading(false))
  }, [])

  const value: AuthContextValue = {
    user,
    loading,
    login: async (email: string, password: string) => setUser(await apiLogin(email, password)),
    signup: async (input: SignupInput) => setUser(await apiSignup(input)),
    logout: async () => {
      await apiLogout()
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
