import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 2,
    duration: '30s',
    thresholds: {
        http_req_duration: ['p(95)<500'],
    },
};

const BASE_URL = 'https://4kjvzmcuh6.execute-api.ap-south-1.amazonaws.com/prod';

export default function () {
    // Test 1: List products
    let res1 = http.get(`${BASE_URL}/api/v1/products`);
    check(res1, {
        'products list: status 200': (r) => r.status === 200,
        'products list: < 300ms': (r) => r.timings.duration < 300,
    });

    // Test 2: Login (form-encoded, OAuth2PasswordRequestForm style)
    let res2 = http.post(`${BASE_URL}/api/v1/users/login`,
        `username=k6test@example.com&password=stringst`,
        {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
    );
    check(res2, {
        'login: status 200': (r) => r.status === 200,
        'login: < 500ms': (r) => r.timings.duration < 500,
    });

    sleep(1);
}