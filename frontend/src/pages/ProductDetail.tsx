import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product, type SizeStock } from '../api'

const STATUS_LABEL: Record<SizeStock['status'], string> = {
  in_stock: 'In stock',
  low: 'Only a few left',
  sold_out: 'Sold out',
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  // Results are tagged with the id they belong to, so a stale item never shows
  // while the next one loads.
  const [result, setResult] = useState<{ id: string; product?: Product; error?: string }>()

  useEffect(() => {
    let current = true
    fetchProduct(productId)
      .then((product) => current && setResult({ id: productId, product }))
      .catch((e: Error) => current && setResult({ id: productId, error: e.message }))
    return () => {
      current = false
    }
  }, [productId])

  const loaded = result?.id === productId ? result : undefined
  const product = loaded?.product
  const error = loaded?.error

  if (error) {
    return (
      <section className="page-header">
        <h1>{error === 'not_found' ? 'Product not found' : 'Something went wrong'}</h1>
        <p className="lead">
          {error === 'not_found'
            ? 'We couldn’t find that item. It may have wandered off campus.'
            : 'We couldn’t load this item. Please try again soon.'}
        </p>
        <Link to="/products" className="btn btn-primary">Back to all products</Link>
      </section>
    )
  }

  if (!product) return <p className="status-msg">Loading…</p>

  const available = product.inventory.filter((s) => s.quantity > 0)

  return (
    <section className="section">
      <Link to="/products" className="back-link">← All products</Link>

      <div className="detail">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <p className="eyebrow">{product.category}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          <dl className="detail-facts">
            <div>
              <dt>Style</dt>
              <dd>{product.garment_type}</dd>
            </div>
            <div>
              <dt>Color</dt>
              <dd>{product.base_color}</dd>
            </div>
            {product.colors.length > 1 && (
              <div>
                <dt>Design colors</dt>
                <dd>{product.colors.join(', ')}</dd>
              </div>
            )}
          </dl>

          <h2 className="detail-subhead">Sizes &amp; stock</h2>
          <p className="muted">
            {available.length > 0
              ? `${product.total_stock} in stock across ${available.length} of ${product.inventory.length} sizes.`
              : 'Currently sold out in every size.'}
          </p>
          <table className="stock-table">
            <thead>
              <tr>
                <th scope="col">Size</th>
                <th scope="col">In stock</th>
                <th scope="col">Availability</th>
              </tr>
            </thead>
            <tbody>
              {product.inventory.map((s) => (
                <tr key={s.size} className={`stock-${s.status}`}>
                  <th scope="row">{s.size}</th>
                  <td>{s.quantity}</td>
                  <td><span className="stock-badge">{STATUS_LABEL[s.status]}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
