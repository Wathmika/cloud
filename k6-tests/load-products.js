import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 10 },  // ramp up to 10 users over 30s
        { duration: '1m', target: 10 },   // stay at 10 users for 1 minute
        { duration: '30s', target: 0 },   // ramp down
    ],
};

const BASE_URL = 'https://4kjvzmcuh6.execute-api.ap-south-1.amazonaws.com/prod';

export default function () {
    const res = http.get(`${BASE_URL}/api/v1/products`);
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    sleep(1);
}