import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { orderApi } from '../api/client'
import { useCart } from '../context/CartContext'

export default function Cart() {
  const { items, removeFromCart, clearCart, total } = useCart()
  const [error, setError] = useState('')
  const [placing, setPlacing] = useState(false)
  const navigate = useNavigate()

  async function handleCheckout() {
    setError('')
    setPlacing(true)
    try {
      // Order Processing accepts one product per order, so checkout
      // places one order per cart line, sequentially.
      for (const item of items) {
        await orderApi.post('/api/v1/orders', {
          product_id: item.product.product_id,
          quantity: item.quantity,
        })
      }
      clearCart()
      navigate('/orders')
    } catch (err) {
      setError(err.response?.data?.detail || 'Checkout failed for one or more items')
    } finally {
      setPlacing(false)
    }
  }

  if (items.length === 0) {
    return (
      <div className="container">
        <h1>Cart</h1>
        <div className="empty-state">Your cart is empty. Go add something from Products.</div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1>Cart</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="card">
        <table>
          <thead>
            <tr><th>Product</th><th>Qty</th><th>Price</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.product.product_id}>
                <td>{item.product.name}</td>
                <td>{item.quantity}</td>
                <td>£{(item.product.price * item.quantity).toFixed(2)}</td>
                <td>
                  <button className="btn-outline btn btn-sm" onClick={() => removeFromCart(item.product.product_id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row-between" style={{ marginTop: 20 }}>
          <strong>Total: £{total.toFixed(2)}</strong>
          <button className="btn" onClick={handleCheckout} disabled={placing}>
            {placing ? 'Placing order…' : 'Checkout'}
          </button>
        </div>
      </div>
    </div>
  )
}
