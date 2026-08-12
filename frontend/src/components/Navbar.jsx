import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const { items } = useCart()
  const navigate = useNavigate()

  return (
    <div className="navbar">
      <Link to="/" className="brand">SmartRetailX</Link>
      <nav>
        <Link to="/products">Products</Link>
        {user && <Link to="/cart">Cart ({items.length})</Link>}
        {user && <Link to="/orders">My Orders</Link>}
        {user?.role === 'admin' && <Link to="/admin/products">Manage Products</Link>}
        {user?.role === 'admin' && <Link to="/admin/inventory">Manage Inventory</Link>}
        {user ? (
          <button
            className="btn-outline btn btn-sm"
            onClick={() => { logout(); navigate('/login') }}
          >
            Log out ({user.email})
          </button>
        ) : (
          <>
            <Link to="/login">Log in</Link>
            <Link to="/register">Sign up</Link>
          </>
        )}
      </nav>
    </div>
  )
}
