import { useEffect, useMemo, useState } from 'react'
import { fetchProducts, type ProductSummary } from '../api'
import { useChatResults } from '../chat-results-context'
import ProductCard from '../components/ProductCard'
import { DanRunner } from '../components/HandsomeDan'

type Sort = 'name' | 'price-asc' | 'price-desc'

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[] | null>(null)
  const [error, setError] = useState(false)
  const { results, query, clear } = useChatResults()

  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')
  const [sort, setSort] = useState<Sort>('name')

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => setError(true))
  }, [])

  const categories = useMemo(() => {
    if (!products) return []
    return [...new Set(products.map((p) => p.category))].sort()
  }, [products])

  const visible = useMemo(() => {
    if (!products) return []
    const term = search.trim().toLowerCase()
    const filtered = products.filter((p) => {
      if (category !== 'all' && p.category !== category) return false
      if (term && !`${p.name} ${p.description}`.toLowerCase().includes(term)) return false
      return true
    })
    const sorted = [...filtered]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price)
    else if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price)
    else sorted.sort((a, b) => a.name.localeCompare(b.name))
    return sorted
  }, [products, search, category, sort])

  return (
    <>
      <section className="page-header">
        <p className="eyebrow">Products</p>
        <h1>Shop Campus Customs</h1>
        <p className="lead">
          Hoodies, crewnecks, tees, quarter-zips, and fleece jackets for every Bulldog.
        </p>
      </section>

      <DanRunner />

      {results.length > 0 && (
        <section className="section results-panel">
          <div className="results-head">
            <div>
              <p className="eyebrow">From your chat</p>
              <h2>{query ? `Results for “${query}”` : 'Picked for you'}</h2>
            </div>
            <button type="button" className="btn btn-outline" onClick={clear}>
              Clear · show all
            </button>
          </div>
          <div className="product-grid">
            {results.map((p) => (
              <ProductCard key={p.product_id} {...p} />
            ))}
          </div>
        </section>
      )}

      <section className="section">
        {results.length > 0 && <h2 className="section-title">All products</h2>}

        <div className="filter-bar">
          <input
            type="search"
            className="filter-search"
            placeholder="Search products…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search products"
          />
          <label className="filter-field">
            <span>Category</span>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="all">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>Sort</span>
            <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
              <option value="name">Name (A–Z)</option>
              <option value="price-asc">Price (low to high)</option>
              <option value="price-desc">Price (high to low)</option>
            </select>
          </label>
        </div>

        {error && <p className="status-msg">We couldn’t load the collection. Please try again soon.</p>}
        {!products && !error && <p className="status-msg">Loading the collection…</p>}

        {products && (
          <>
            <p className="result-count">
              {visible.length} {visible.length === 1 ? 'item' : 'items'}
              {(search || category !== 'all') && ` of ${products.length}`}
            </p>
            {visible.length === 0 ? (
              <p className="status-msg">No products match your filters. Try clearing the search.</p>
            ) : (
              <div className="product-grid">
                {visible.map((p) => (
                  <ProductCard key={p.product_id} {...p} />
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </>
  )
}
