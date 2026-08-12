import axios from 'axios'

const USER_API = import.meta.env.VITE_USER_API || 'http://localhost:8001'
const PRODUCT_API = import.meta.env.VITE_PRODUCT_API || 'http://localhost:8002'
const INVENTORY_API = import.meta.env.VITE_INVENTORY_API || 'http://localhost:8003'
const ORDER_API = import.meta.env.VITE_ORDER_API || 'http://localhost:8005'

function withAuth(baseURL) {
  const instance = axios.create({ baseURL })
  instance.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  return instance
}

export const userApi = withAuth(USER_API)
export const productApi = withAuth(PRODUCT_API)
export const inventoryApi = withAuth(INVENTORY_API)
export const orderApi = withAuth(ORDER_API)
