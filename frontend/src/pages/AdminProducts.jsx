import { useEffect, useState } from 'react'
import { productApi } from '../api/client'

const emptyForm = { name: '', description: '', price: '', category: '' }

export default function AdminProducts() {
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')

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
    setForm({ name: p.name, description: p.description, price: p.price, category: p.category })
  }

  async function handleDelete(id) {
    await productApi.delete(`/api/v1/products/${id}`)
    load()
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
              <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required />
            </div>
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
          </div>
          <div className="form-group">
            <label>Price (£)</label>
            <input type="number" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
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
                <td>£{p.price}</td>
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
