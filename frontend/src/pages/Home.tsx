import { Link } from 'react-router-dom'
import HandsomeDan from '../components/HandsomeDan'

const HIGHLIGHTS = [
  {
    title: 'Everyone belongs here',
    text: 'First-years and fifth-years, grad students and grandparents, alumni and admitted students: if you love Yale, you’re family.',
  },
  {
    title: 'Many stories, one community',
    text: 'Yale is made of people from every background, hometown, and walk of life. Our gear celebrates all of you.',
  },
  {
    title: 'Bulldog Blue, head to toe',
    text: 'From residential-college crewnecks to game-day hoodies, show your colors whether you’re on Old Campus or across the world.',
  },
]

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <HandsomeDan size={120} className="hero-dan dan-hop" label="Handsome Dan, the Yale bulldog" />
          <p className="eyebrow">Welcome to Campus Customs</p>
          <h1>Come as you are.<br />You’re already family.</h1>
          <p className="lead">
            Whether you’re visiting New Haven for the first time or coming home for your
            twenty-fifth reunion, we’re so glad you’re here. Find the Yale gear that feels
            like <em>you</em>, and wear your Bulldog Blue with pride.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary">Shop the collection</Link>
            <Link to="/about" className="btn btn-outline">Our story</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">A place for every Bulldog</h2>
        <div className="card-grid">
          {HIGHLIGHTS.map((h) => (
            <article key={h.title} className="card">
              <h3>{h.title}</h3>
              <p>{h.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section band">
        <h2>Join the Bulldog family</h2>
        <p>
          Create an account to save your favorites and chat with our shopping assistant
          about sizes, styles, and the perfect gift.
        </p>
        <Link to="/signup" className="btn btn-primary">Create an account</Link>
      </section>
    </>
  )
}
