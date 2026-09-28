import { DanRunner } from '../components/HandsomeDan'

const VALUES = [
  {
    title: 'Community',
    text: 'We started Campus Customs because a sweatshirt can be a conversation starter, a care package, or a hug from home. Every piece we carry is meant to bring Bulldogs together.',
  },
  {
    title: 'Diversity',
    text: 'Yale’s strength is its people: students, scholars, staff, and neighbors from every culture, identity, and corner of the globe. We want everyone to see themselves in Yale blue.',
  },
  {
    title: 'Bulldog Blue',
    text: 'Our favorite color is the one you’ll see everywhere from Cross Campus to the Yale Bowl. We wear it for game days, graduation days, and every ordinary Tuesday in between.',
  },
]

export default function About() {
  return (
    <>
      <section className="page-header">
        <p className="eyebrow">About Us</p>
        <h1>Made for the whole Yale family</h1>
        <p className="lead">
          Campus Customs is a small shop with a big welcome. We celebrate the students who
          call New Haven home, the families cheering them on, the alumni who never stopped
          being Bulldogs, and everyone who’s ever dreamed of walking through Phelps Gate.
        </p>
      </section>

      <DanRunner />

      <section className="section">
        <div className="card-grid">
          {VALUES.map((v) => (
            <article key={v.title} className="card">
              <h3>{v.title}</h3>
              <p>{v.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section band">
        <h2>You’re invited</h2>
        <p>
          Thinking about applying? Visiting for the weekend? Sending love to someone on
          campus? However you’re connected to Yale, there’s a place for you here. Come
          visit, say hello, and find something that makes you proud to be a Bulldog.
        </p>
      </section>
    </>
  )
}
