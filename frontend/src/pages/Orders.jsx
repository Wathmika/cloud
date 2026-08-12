import { useEffect, useState } from 'react'
import { orderApi } from '../api/client'

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    orderApi.get('/api/v1/orders').then((res) => {
      setOrders(res.data.slice().reverse())
      setLoading(false)
    })
  }, [])

  return (
    <div className="container">
      <h1>My Orders</h1>
      {loading && <p>Loading…</p>}
      {!loading && orders.length === 0 && <div className="empty-state">No orders yet.</div>}

      {orders.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr><th>Order</th><th>Product</th><th>Qty</th><th>Total</th><th>Status</th><th>Placed</th></tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td>#{o.id}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{o.product_id.slice(0, 8)}…</td>
                  <td>{o.quantity}</td>
                  <td>£{o.total_amount}</td>
                  <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
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
