import { useEffect, useState } from 'react'
import { productApi } from '../api/client'

const emptyForm = { name: '', description: '', price: '', category: '', image_url: '' }

export default function AdminProducts() {
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [promoForm, setPromoForm] = useState({ product_id: '', discount_percentage: '', start_time: '', end_time: '' })
  const [promoMessage, setPromoMessage] = useState('')
  const [promoError, setPromoError] = useState('')

  const categories = [...new Set(products.map((p) => p.category))]

  function load() {
    productApi.get('/api/v1/products').then((res) => setProducts(res.data))
  }

  useEffect(load, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const payload = { ...form, price: Number(form.price) }
      if (editingId) {
        await productApi.put(`/api/v1/products/${editingId}`, payload)
      } else {
        await productApi.post('/api/v1/products', payload)
      }
      setForm(emptyForm)
      setEditingId(null)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    }
  }

  function startEdit(p) {
    setEditingId(p.product_id)
    setForm({ name: p.name, description: p.description, price: p.price, category: p.category, image_url: p.image_url || '' })
  }

  async function handleDelete(id) {
    await productApi.delete(`/api/v1/products/${id}`)
    load()
  }

  async function handlePromoSubmit(e) {
    e.preventDefault()
    setPromoError('')
    setPromoMessage('')
    try {
      await productApi.post(`/api/v1/products/${promoForm.product_id}/promotions`, {
        discount_percentage: Number(promoForm.discount_percentage),
        start_time: new Date(promoForm.start_time).toISOString(),
        end_time: new Date(promoForm.end_time).toISOString(),
      })
      setPromoMessage('Promotion set successfully')
      setPromoForm({ product_id: '', discount_percentage: '', start_time: '', end_time: '' })
      load()
    } catch (err) {
      setPromoError(err.response?.data?.detail || 'Failed to set promotion')
    }
  }

  return (
    <div className="container">
      <h1>Manage Products</h1>
      <p className="subtitle">Admin only — create, edit, and remove catalogue items</p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>{editingId ? 'Edit product' : 'Add product'}</h3>
        <form onSubmit={handleSubmit}>
          <div className="row">
            <div className="form-group" style={{ flex: 1 }}>
              <label>Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Category</label>
              <select
                value={categories.includes(form.category) ? form.category : '__new__'}
                onChange={(e) => setForm({ ...form, category: e.target.value === '__new__' ? '' : e.target.value })}
              >
                <option value="">Select a category…</option>
                {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                <option value="__new__">+ Add new category</option>
              </select>
              {(!categories.includes(form.category) || form.category === '') && (
                <input
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  placeholder="New category name"
                  style={{ marginTop: 8 }}
                  required
                />
              )}
            </div>
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Price (Rs.)</label>
            <input type="number" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Image URL</label>
            <input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." />
          </div>
          <div className="row">
            <button className="btn" type="submit">{editingId ? 'Save changes' : 'Add product'}</button>
            {editingId && (
              <button type="button" className="btn-outline btn" onClick={() => { setEditingId(null); setForm(emptyForm) }}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Set Promotion</h3>
        {promoMessage && <div className="alert alert-success">{promoMessage}</div>}
        {promoError && <div className="alert alert-error">{promoError}</div>}
        <form onSubmit={handlePromoSubmit}>
          <div className="form-group">
            <label>Product</label>
            <select
              value={promoForm.product_id}
              onChange={(e) => setPromoForm({ ...promoForm, product_id: e.target.value })}
              required
            >
              <option value="">Select a product…</option>
              {products.map((p) => (
                <option key={p.product_id} value={p.product_id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="row">
            <div className="form-group" style={{ flex: 1 }}>
              <label>Discount (%)</label>
              <input
                type="number"
                step="1"
                min="1"
                max="100"
                value={promoForm.discount_percentage}
                onChange={(e) => setPromoForm({ ...promoForm, discount_percentage: e.target.value })}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Start Time</label>
              <input
                type="datetime-local"
                value={promoForm.start_time}
                onChange={(e) => setPromoForm({ ...promoForm, start_time: e.target.value })}
                required
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>End Time</label>
              <input
                type="datetime-local"
                value={promoForm.end_time}
                onChange={(e) => setPromoForm({ ...promoForm, end_time: e.target.value })}
                required
              />
            </div>
          </div>
          <button className="btn" type="submit">Set Promotion</button>
        </form>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Name</th><th>Category</th><th>Price</th><th></th></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.product_id}>
                <td>{p.name}</td>
                <td>{p.category}</td>
                <td>Rs. {p.price}</td>
                <td className="row">
                  <button className="btn-outline btn btn-sm" onClick={() => startEdit(p)}>Edit</button>
                  <button className="btn-danger btn btn-sm" onClick={() => handleDelete(p.product_id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}