import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { productApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function ProductDetail() {
  const { id } = useParams()
  const [product, setProduct] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState(false)
  const { user } = useAuth()
  const { addToCart } = useCart()
  const navigate = useNavigate()

  useEffect(() => {
    productApi.get(`/api/v1/products/${id}`).then((res) => setProduct(res.data))
  }, [id])

  if (!product) return <div className="container"><p>Loading…</p></div>

  function handleAdd() {
    if (!user) { navigate('/login'); return }
    addToCart(product, quantity)
    setAdded(true)
    setTimeout(() => setAdded(false), 1500)
  }

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 480 }}>
        {product.image_url && (
          <img src={product.image_url} alt={product.name} style={{ width: '100%', borderRadius: 8, marginBottom: 12 }} />
        )}
        <span className="category">{product.category}</span>
        <h1>{product.name}</h1>
        <p style={{ color: 'var(--text-muted)' }}>{product.description}</p>

        {product.discount_percentage ? (
          <div>
            <span style={{ textDecoration: 'line-through', color: 'var(--text-muted)', fontSize: 16 }}>
              Rs. {product.original_price}
            </span>{' '}
            <span className="price" style={{ fontSize: 24 }}>Rs. {product.price}</span>{' '}
            <span className="badge badge-confirmed">-{product.discount_percentage}% OFF</span>
          </div>
        ) : (
          <p className="price" style={{ fontSize: 24 }}>Rs. {product.price}</p>
        )}

        <div className="row" style={{ marginTop: 16 }}>
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            style={{ width: 70, padding: 8, border: '1px solid var(--border)', borderRadius: 8 }}
          />
          <button className="btn" onClick={handleAdd}>
            {added ? 'Added ✓' : 'Add to cart'}
          </button>
        </div>
      </div>
    </div>
  )
}