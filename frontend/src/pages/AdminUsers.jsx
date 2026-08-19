import { useEffect, useState } from 'react'
import { userApi } from '../api/client'

export default function AdminUsers() {
    const [users, setUsers] = useState([])

    function load() {
        userApi.get('/api/v1/users').then((res) => setUsers(res.data))
    }

    useEffect(load, [])

    async function toggleRole(userId, currentRole) {
        const newRole = currentRole === 'admin' ? 'customer' : 'admin'
        await userApi.patch(`/api/v1/users/${userId}/role?role=${newRole}`)
        load()
    }

    return (
        <div className="container">
            <h1>Manage users</h1>
            <p className="subtitle">Admin only — view accounts and change roles</p>
            <div className="card">
                <table>
                    <thead>
                        <tr><th>Email</th><th>Name</th><th>Role</th><th></th></tr>
                    </thead>
                    <tbody>
                        {users.map((u) => (
                            <tr key={u.id}>
                                <td>{u.email}</td>
                                <td>{u.full_name}</td>
                                <td><span className={`badge badge-${u.role === 'admin' ? 'confirmed' : 'packed'}`}>{u.role}</span></td>
                                <td>
                                    <button className="btn-outline btn btn-sm" onClick={() => toggleRole(u.id, u.role)}>
                                        {u.role === 'admin' ? 'Remove admin' : 'Make admin'}
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}