import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { orderApi } from '../api/client'
import { useCart } from '../context/CartContext'

function formatCardNumber(value) {
    return value.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim()
}

function formatExpiry(value) {
    const digits = value.replace(/\D/g, '').slice(0, 4)
    if (digits.length >= 3) return `${digits.slice(0, 2)}/${digits.slice(2)}`
    return digits
}

export default function Payment() {
    const { items, clearCart, total } = useCart()
    const [card, setCard] = useState({ number: '', name: '', expiry: '', cvv: '' })
    const [error, setError] = useState('')
    const [placing, setPlacing] = useState(false)
    const navigate = useNavigate()

    function validCard() {
        const digits = card.number.replace(/\s/g, '')
        return digits.length === 16 && card.name.trim().length > 0 &&
            /^\d{2}\/\d{2}$/.test(card.expiry) && /^\d{3,4}$/.test(card.cvv)
    }

    async function handlePay(e) {
        e.preventDefault()
        setError('')
        if (!validCard()) {
            setError('Please check your card details — all fields are required and must be valid.')
            return
        }
        setPlacing(true)
        try {
            for (const item of items) {
                await orderApi.post('/api/v1/orders', {
                    product_id: item.product.product_id,
                    quantity: item.quantity,
                })
            }
            clearCart()
            navigate('/orders')
        } catch (err) {
            setError(err.response?.data?.detail || 'Payment failed for one or more items')
        } finally {
            setPlacing(false)
        }
    }

    if (items.length === 0) {
        return (
            <div className="container">
                <div className="empty-state">Your cart is empty.</div>
            </div>
        )
    }

    return (
        <div className="container">
            <div className="card auth-card">
                <h1>Payment</h1>
                <p className="subtitle">Total: Rs. {total.toFixed(2)}</p>
                {error && <div className="alert alert-error">{error}</div>}
                <form onSubmit={handlePay}>
                    <div className="form-group">
                        <label>Card number</label>
                        <input
                            placeholder="1234 5678 9012 3456"
                            value={card.number}
                            onChange={(e) => setCard({ ...card, number: formatCardNumber(e.target.value) })}
                            maxLength={19}
                            required
                        />
                    </div>
                    <div className="form-group">
                        <label>Name on card</label>
                        <input value={card.name} onChange={(e) => setCard({ ...card, name: e.target.value })} required />
                    </div>
                    <div className="row">
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Expiry</label>
                            <input
                                placeholder="MM/YY"
                                value={card.expiry}
                                onChange={(e) => setCard({ ...card, expiry: formatExpiry(e.target.value) })}
                                maxLength={5}
                                required
                            />
                        </div>
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>CVV</label>
                            <input
                                placeholder="123"
                                value={card.cvv}
                                onChange={(e) => setCard({ ...card, cvv: e.target.value.replace(/\D/g, '').slice(0, 4) })}
                                maxLength={4}
                                required
                            />
                        </div>
                    </div>
                    <button className="btn" type="submit" disabled={placing} style={{ width: '100%' }}>
                        {placing ? 'Processing…' : `Pay Rs. ${total.toFixed(2)}`}
                    </button>
                </form>
                <p style={{ marginTop: 16, fontSize: 12, color: 'var(--text-muted)' }}>
                    This is a simulated payment for demonstration purposes. No real card data is transmitted or stored.
                </p>
            </div>
        </div>
    )
}