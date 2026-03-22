'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useUser } from '@/lib/UserContext'

export default function Header() {
  const { username, isLoaded, login, logout } = useUser()
  const [inputName, setInputName] = useState('')
  const [showInput, setShowInput] = useState(false)

  function handleLogin() {
    const name = inputName.trim()
    if (name) {
      login(name)
      setInputName('')
      setShowInput(false)
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg no-underline">
          <span>🧬</span>
          <span>BioJSON</span>
        </Link>
        <div className="flex items-center gap-4">
          <nav className="flex items-center gap-4 text-sm text-[var(--muted-foreground)]">
            <Link href="/" className="hover:text-[var(--foreground)] no-underline">论文列表</Link>
          </nav>
          {!isLoaded ? (
            <span className="text-sm text-[var(--muted-foreground)]">加载中...</span>
          ) : username ? (
            <div className="flex items-center gap-2 text-sm">
              <span className="px-2 py-1 rounded bg-[var(--muted)] border border-[var(--border)]">
                User: <strong>{username}</strong>
              </span>
              <button
                onClick={logout}
                className="px-3 py-1 rounded border border-[var(--border)] hover:bg-[var(--muted)] cursor-pointer text-sm"
              >
                Logout
              </button>
            </div>
          ) : showInput ? (
            <div className="flex items-center gap-2">
              <input
                value={inputName}
                onChange={(e) => setInputName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                placeholder="输入用户名"
                className="px-2 py-1 text-sm rounded border border-[var(--border)] bg-[var(--background)] w-32"
                autoFocus
              />
              <button
                onClick={handleLogin}
                disabled={!inputName.trim()}
                className="px-3 py-1 text-sm rounded bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90 disabled:opacity-50 cursor-pointer"
              >
                登录
              </button>
              <button
                onClick={() => setShowInput(false)}
                className="px-2 py-1 text-sm rounded border border-[var(--border)] hover:bg-[var(--muted)] cursor-pointer"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowInput(true)}
              className="px-3 py-1 text-sm rounded border border-[var(--border)] hover:bg-[var(--muted)] cursor-pointer"
            >
              登录
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
