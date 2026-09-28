import { Link } from 'react-router-dom'
import { formatPrice } from '../api'

interface ProductCardProps {
  product_id: string
  name: string
  price: number
  image_url: string
  description?: string
  total_stock?: number
}

/** Turn a total-stock number into a shopper-facing availability badge. */
function stockBadge(total: number | undefined) {
  if (total === undefined) return null
  if (total === 0) return { label: 'Sold out', className: 'badge-sold-out' }
  if (total <= 15) return { label: 'Low stock', className: 'badge-low' }
  return { label: 'In stock', className: 'badge-in' }
}

/** A catalogue product card. Clicking it opens the single-item page. */
export default function ProductCard({
  product_id,
  name,
  price,
  image_url,
  description,
  total_stock,
}: ProductCardProps) {
  const badge = stockBadge(total_stock)
  return (
    <Link to={`/products/${product_id}`} className="product-card">
      <div className="product-card-image">
        {badge && <span className={`stock-pill ${badge.className}`}>{badge.label}</span>}
        <img src={image_url} alt={name} loading="lazy" />
      </div>
      <div className="product-card-body">
        <h3>{name}</h3>
        {description && <p className="product-card-desc">{description}</p>}
        <p className="product-card-price">{formatPrice(price)}</p>
      </div>
    </Link>
  )
}
