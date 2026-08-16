import { useEffect, useState } from 'react'
import { orderApi, productApi } from '../api/client'

const STATUSES = ['confirmed', 'packed', 'shipped', 'delivered', 'cancelled']

export default function AdminOrders() {
    const [orders, setOrders] = useState([])
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)

    function load() {
        Promise.all([
            orderApi.get('/api/v1/orders/all'),
            productApi.get('/api/v1/products'),
        ]).then(([ordersRes, productsRes]) => {
            setOrders(ordersRes.data)
            setProducts(productsRes.data)
            setLoading(false)
        })
    }

    useEffect(load, [])

    function productName(productId) {
        return products.find((p) => p.product_id === productId)?.name || 'Unknown product'
    }

    async function handleStatusChange(orderId, newStatus) {
        await orderApi.patch(`/api/v1/orders/${orderId}/status`, { status: newStatus })
        load()
    }

    return (
        <div className="container">
            <h1>All Orders</h1>
            <p className="subtitle">Admin only — manage delivery status</p>
            {loading && <p>Loading…</p>}
            {!loading && (
                <div className="card">
                    <table>
                        <thead>
                            <tr><th>Order</th><th>Product</th><th>Customer ID</th><th>Qty</th><th>Total</th><th>Status</th><th>Update</th></tr>
                        </thead>
                        <tbody>
                            {orders.map((o) => (
                                <tr key={o.id}>
                                    <td>#{o.id}</td>
                                    <td>{productName(o.product_id)}</td>
                                    <td>{o.user_id}</td>
                                    <td>{o.quantity}</td>
                                    <td>Rs. {o.total_amount}</td>
                                    <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                                    <td>
                                        <select value={o.status} onChange={(e) => handleStatusChange(o.id, e.target.value)}>
                                            {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    )
}