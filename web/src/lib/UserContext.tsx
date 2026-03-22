'use client'

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface UserContextType {
  username: string | null
  isLoaded: boolean
  setUsername: (name: string | null) => void
  login: (name: string) => void
  logout: () => void
}

const UserContext = createContext<UserContextType>({
  username: null,
  isLoaded: false,
  setUsername: () => {},
  login: () => {},
  logout: () => {},
})

export function UserProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('biojson_username')
    if (saved) setUsername(saved)
    setIsLoaded(true)
  }, [])

  function login(name: string) {
    localStorage.setItem('biojson_username', name)
    setUsername(name)
  }

  function logout() {
    localStorage.removeItem('biojson_username')
    setUsername(null)
  }

  return (
    <UserContext.Provider value={{ username, isLoaded, setUsername, login, logout }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
