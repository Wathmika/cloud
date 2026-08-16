import { useEffect, useState } from 'react'
import { orderApi, productApi } from '../api/client'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      orderApi.get('/api/v1/orders'),
      productApi.get('/api/v1/products'),
    ]).then(([ordersRes, productsRes]) => {
      setOrders(ordersRes.data.slice().reverse())
      setProducts(productsRes.data)
      setLoading(false)
    })
  }, [])

  function productName(productId) {
    return products.find((p) => p.product_id === productId)?.name || 'Unknown product'
  }

  return (
    <div className="container">
      <h1>My Orders</h1>
      {loading && <p>Loading…</p>}
      {!loading && orders.length === 0 && <div className="empty-state">No orders yet.</div>}

      {orders.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr><th>Order</th><th>Product</th><th>Qty</th><th>Total</th><th>Status</th><th>Tracking</th><th>Placed</th></tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td>{productName(o.product_id)}</td>
                  <td>{o.quantity}</td>
                  <td>Rs. {o.total_amount}</td>
                  <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                  <td>{o.tracking_number || '—'}</td>
                  <td>{new Date(o.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}