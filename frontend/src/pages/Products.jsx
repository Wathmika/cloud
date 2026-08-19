import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { productApi } from '../api/client'

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('all')

  useEffect(() => {
    productApi.get('/api/v1/products').then((res) => {
      setProducts(res.data)
      setLoading(false)
    })
  }, [])

  const categories = ['all', ...new Set(products.map((p) => p.category))]
  const filtered = category === 'all' ? products : products.filter((p) => p.category === category)

  return (
    <div className="container">
      <h1>Products</h1>
      <p className="subtitle">Browse the SmartRetailX catalogue</p>

      {!loading && products.length > 0 && (
        <div className="row" style={{ marginBottom: 20, flexWrap: 'wrap', gap: 8 }}>
          {categories.map((c) => (
            <button
              key={c}
              className={c === category ? 'btn btn-sm' : 'btn-outline btn btn-sm'}
              onClick={() => setCategory(c)}
            >
              {c === 'all' ? 'All' : c}
            </button>
          ))}
        </div>
      )}

      {loading && <p>Loading…</p>}
      {!loading && filtered.length === 0 && (
        <div className="empty-state">No products in this category.</div>
      )}

      <div className="grid">
        {filtered.map((p) => (
          <Link key={p.product_id} to={`/products/${p.product_id}`} className="product-card">
            {p.image_url && (
              <img src={p.image_url} alt={p.name} style={{ width: '100%', height: 200, objectFit: 'cover', borderRadius: 6, marginBottom: 4 }} />
            )}
            <span className="category">{p.category}</span>
            <h3>{p.name}</h3>
            {p.discount_percentage ? (
              <div>
                <span style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: 13 }}>
                  Rs. {p.original_price}
                </span>{' '}
                <span className="price">Rs. {p.price}</span>{' '}
                <span className="badge badge-confirmed">-{p.discount_percentage}%</span>
              </div>
            ) : (
              <span className="price">Rs. {p.price}</span>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}