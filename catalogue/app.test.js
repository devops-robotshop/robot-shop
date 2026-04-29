const request = require('supertest');
const { app, setMongo } = require('./app');

beforeEach(() => {
    setMongo(false, null);
});

describe('GET /health', () => {
    test('returns 200 with app OK', async () => {
        const res = await request(app).get('/health');
        expect(res.status).toBe(200);
        expect(res.body.app).toBe('OK');
    });

    test('reports mongo: false when DB not connected', async () => {
        const res = await request(app).get('/health');
        expect(res.body.mongo).toBe(false);
    });
});

describe('GET /products', () => {
    test('returns 500 when DB not connected', async () => {
        const res = await request(app).get('/products');
        expect(res.status).toBe(500);
    });

    test('returns product list when DB is connected', async () => {
        const mockProducts = [{ sku: 'A1', name: 'Widget', price: 9.99 }];
        const mockCollection = {
            find: jest.fn().mockReturnValue({
                toArray: jest.fn().mockResolvedValue(mockProducts)
            })
        };
        setMongo(true, mockCollection);

        const res = await request(app).get('/products');
        expect(res.status).toBe(200);
        expect(res.body).toEqual(mockProducts);
    });
});
