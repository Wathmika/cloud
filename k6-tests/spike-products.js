import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '10s', target: 5 },    // baseline
        { duration: '5s', target: 80 },    // sudden spike
        { duration: '30s', target: 80 },   // hold at spike
        { duration: '10s', target: 5 },    // sudden drop
        { duration: '10s', target: 0 },
    ],
};

const BASE_URL = 'https://4kjvzmcuh6.execute-api.ap-south-1.amazonaws.com/prod';

export default function () {
    const res = http.get(`${BASE_URL}/api/v1/products`);
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    sleep(0.3);
}