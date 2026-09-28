import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth-context'

const MAIN_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()
  const close = () => setOpen(false)
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'nav-link active' : 'nav-link'

  async function handleLogout() {
    close()
    await logout()
    navigate('/')
  }

  return (
    <header className="navbar">
      <nav className="navbar-inner" aria-label="Main">
        <Link to="/" className="brand" onClick={close}>
          <span className="brand-mark" aria-hidden="true">Y</span>
          Campus Customs
        </Link>

        <button
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="nav-menu"
          onClick={() => setOpen(!open)}
        >
          <span className="sr-only">Toggle menu</span>
          <span aria-hidden="true">☰</span>
        </button>

        <div id="nav-menu" className={open ? 'nav-menu open' : 'nav-menu'}>
          <ul className="nav-links">
            {MAIN_LINKS.map((link) => (
              <li key={link.to}>
                <NavLink to={link.to} end={link.to === '/'} className={linkClass} onClick={close}>
                  {link.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <div className="nav-auth">
            {loading ? null : user ? (
              <>
                <span className="nav-greeting">Hi, {user.first_name ?? user.name}!</span>
                <button type="button" className="btn btn-outline" onClick={handleLogout}>
                  Log Out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className={linkClass} onClick={close}>
                  Log In
                </NavLink>
                <NavLink to="/signup" className="btn btn-primary" onClick={close}>
                  Create Account
                </NavLink>
              </>
            )}
          </div>
        </div>
      </nav>
    </header>
  )
}
