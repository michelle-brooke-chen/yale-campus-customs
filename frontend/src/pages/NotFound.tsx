import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="page-header">
      <h1>Page not found</h1>
      <p className="lead">This path wandered off campus.</p>
      <Link to="/" className="btn btn-primary">Back to Home</Link>
    </section>
  )
}
