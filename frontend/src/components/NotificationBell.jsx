import { useEffect, useState } from 'react'
import { orderApi } from '../api/client'

export default function NotificationBell() {
    const [notifications, setNotifications] = useState([])
    const [open, setOpen] = useState(false)

    function load() {
        orderApi.get('/api/v1/notifications').then((res) => setNotifications(res.data))
    }

    useEffect(load, [])

    const unreadCount = notifications.filter((n) => !n.is_read).length

    async function handleOpen() {
        setOpen(!open)
        if (!open) load()
    }

    async function markRead(id) {
        await orderApi.patch(`/api/v1/notifications/${id}/read`)
        load()
    }

    return (
        <div style={{ position: 'relative' }}>
            <button className="btn-outline btn btn-sm" onClick={handleOpen}>
                🔔 {unreadCount > 0 && <span className="badge badge-pending">{unreadCount}</span>}
            </button>
            {open && (
                <div className="card" style={{
                    position: 'absolute', right: 0, top: '110%', width: 300, zIndex: 10,
                    maxHeight: 320, overflowY: 'auto',
                }}>
                    {notifications.length === 0 && <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No notifications</p>}
                    {notifications.map((n) => (
                        <div
                            key={n.id}
                            onClick={() => !n.is_read && markRead(n.id)}
                            style={{
                                padding: '8px 0', borderBottom: '1px solid var(--border)',
                                fontSize: 13, cursor: n.is_read ? 'default' : 'pointer',
                                opacity: n.is_read ? 0.6 : 1,
                            }}
                        >
                            {n.message}
                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                {new Date(n.created_at).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}