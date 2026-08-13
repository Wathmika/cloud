import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { productApi } from '../api/client'

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    productApi.get('/api/v1/products').then((res) => {
      setProducts(res.data)
      setLoading(false)
    })
  }, [])

  return (
    <div className="container">
      <h1>Products</h1>
      <p className="subtitle">Browse the SmartRetailX catalogue</p>

      {loading && <p>Loading…</p>}
      {!loading && products.length === 0 && (
        <div className="empty-state">No products yet.</div>
      )}

      <div className="grid">
        {products.map((p) => (
          <Link key={p.product_id} to={`/products/${p.product_id}`} className="product-card">
            <span className="category">{p.category}</span>
            <h3>{p.name}</h3>
            <span className="price">Rs.{p.price}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
