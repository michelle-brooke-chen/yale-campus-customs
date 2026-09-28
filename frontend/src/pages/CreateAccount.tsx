import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthError } from '../api'
import { useAuth } from '../auth-context'

const EMPTY = {
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  confirm_password: '',
}

export default function CreateAccount() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const update = (field: keyof typeof EMPTY) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setBusy(true)
    try {
      await signup(form)
      navigate('/')
    } catch (err) {
      setError(err instanceof AuthError ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="auth">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Join the Bulldog family</h1>
        <p className="muted">It only takes a minute, and everyone is welcome.</p>

        {error && <p className="form-error" role="alert">{error}</p>}

        <div className="form-row">
          <label>
            First name
            <input
              type="text"
              autoComplete="given-name"
              value={form.first_name}
              onChange={update('first_name')}
              required
            />
          </label>
          <label>
            Last name
            <input
              type="text"
              autoComplete="family-name"
              value={form.last_name}
              onChange={update('last_name')}
              required
            />
          </label>
        </div>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={form.email}
            onChange={update('email')}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={update('password')}
            minLength={8}
            required
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            autoComplete="new-password"
            value={form.confirm_password}
            onChange={update('confirm_password')}
            minLength={8}
            required
          />
        </label>

        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="muted small">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
