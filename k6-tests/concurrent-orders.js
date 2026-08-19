import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '20s',
};

const BASE_URL = 'https://4kjvzmcuh6.execute-api.ap-south-1.amazonaws.com/prod';

export function setup() {
    const loginRes = http.post(`${BASE_URL}/api/v1/users/login`,
        `username=k6test@example.com&password=stringst`,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    const token = loginRes.json('access_token');
    return { token };
}

export default function (data) {
    const res = http.post(`${BASE_URL}/api/v1/orders`,
        JSON.stringify({ product_id: '2dc80da2-626c-454e-b68e-538d3d48c5df', quantity: 1 }),
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${data.token}`,
            },
        }
    );
    check(res, {
        'order: 200 or 409 (expected outcomes)': (r) => r.status === 200 || r.status === 409,
        'order: not a 500 error': (r) => r.status !== 500,
    });
    sleep(1);
}