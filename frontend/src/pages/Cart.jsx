import { useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'

export default function Cart() {
  const { items, removeFromCart, total } = useCart()
  const navigate = useNavigate()

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
                <td>Rs. {(item.product.price * item.quantity).toFixed(2)}</td>
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
          <strong>Total: Rs. {total.toFixed(2)}</strong>
          <button className="btn" onClick={() => navigate('/payment')}>
            Proceed to Payment
          </button>
        </div>
      </div>
    </div>
  )
}