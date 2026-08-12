import { useEffect, useState } from 'react'
import { inventoryApi, productApi } from '../api/client'

export default function AdminInventory() {
  const [inventory, setInventory] = useState([])
  const [products, setProducts] = useState([])
  const [newRecord, setNewRecord] = useState({ product_id: '', quantity_available: '' })
  const [editValues, setEditValues] = useState({}) // productId -> value being typed
  const [error, setError] = useState('')

  function load() {
    inventoryApi.get('/api/v1/inventory').then((res) => setInventory(res.data))
    productApi.get('/api/v1/products').then((res) => setProducts(res.data))
  }

  useEffect(load, [])

  function productName(productId) {
    return products.find((p) => p.product_id === productId)?.name || productId.slice(0, 8) + '…'
  }

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    try {
      await inventoryApi.post('/api/v1/inventory', {
        product_id: newRecord.product_id,
        quantity_available: Number(newRecord.quantity_available),
      })
      setNewRecord({ product_id: '', quantity_available: '' })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create inventory record')
    }
  }

  async function handleUpdate(productId) {
    const value = editValues[productId]
    if (value === undefined || value === '') return
    await inventoryApi.put(`/api/v1/inventory/${productId}`, { quantity_available: Number(value) })
    setEditValues((prev) => ({ ...prev, [productId]: undefined }))
    load()
  }

  const productsWithoutInventory = products.filter(
    (p) => !inventory.some((i) => i.product_id === p.product_id)
  )

  return (
    <div className="container">
      <h1>Manage Inventory</h1>
      <p className="subtitle">Admin only — stock levels per product</p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Create inventory record</h3>
        <form onSubmit={handleCreate}>
          <div className="row">
            <div className="form-group" style={{ flex: 2 }}>
              <label>Product</label>
              <select
                value={newRecord.product_id}
                onChange={(e) => setNewRecord({ ...newRecord, product_id: e.target.value })}
                required
              >
                <option value="">Select a product…</option>
                {productsWithoutInventory.map((p) => (
                  <option key={p.product_id} value={p.product_id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label>Starting stock</label>
              <input
                type="number"
                min={0}
                value={newRecord.quantity_available}
                onChange={(e) => setNewRecord({ ...newRecord, quantity_available: e.target.value })}
                required
              />
            </div>
          </div>
          <button className="btn" type="submit">Create record</button>
        </form>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Product</th><th>Stock available</th><th></th></tr>
          </thead>
          <tbody>
            {inventory.map((i) => (
              <tr key={i.product_id}>
                <td>{productName(i.product_id)}</td>
                <td>{i.quantity_available}</td>
                <td className="row">
                  <input
                    type="number"
                    min={0}
                    placeholder="New value"
                    style={{ width: 90, padding: 6, border: '1px solid var(--border)', borderRadius: 6 }}
                    value={editValues[i.product_id] ?? ''}
                    onChange={(e) => setEditValues((prev) => ({ ...prev, [i.product_id]: e.target.value }))}
                  />
                  <button className="btn btn-sm" onClick={() => handleUpdate(i.product_id)}>Update</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
