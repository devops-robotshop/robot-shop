const { mergeList, calcTotal, calcTax } = require('./helpers');

describe('calcTotal', () => {
    test('returns 0 for empty list', () => {
        expect(calcTotal([])).toBe(0);
    });

    test('returns subtotal for single item', () => {
        const list = [{ sku: 'A1', qty: 2, price: 50, subtotal: 100 }];
        expect(calcTotal(list)).toBe(100);
    });

    test('sums subtotals for multiple items', () => {
        const list = [
            { sku: 'A1', qty: 1, price: 100, subtotal: 100 },
            { sku: 'B2', qty: 2, price: 25,  subtotal: 50  },
            { sku: 'C3', qty: 3, price: 10,  subtotal: 30  }
        ];
        expect(calcTotal(list)).toBe(180);
    });
});

describe('calcTax', () => {
    test('returns 20 for total 120', () => {
        expect(calcTax(120)).toBeCloseTo(20);
    });

    test('returns 0 for total 0', () => {
        expect(calcTax(0)).toBe(0);
    });
});

describe('mergeList', () => {
    test('adds new item when sku not in list', () => {
        const list = [];
        const product = { sku: 'NEW1', name: 'Widget', price: 10, qty: 2, subtotal: 20 };
        const result = mergeList(list, product, 2);
        expect(result).toHaveLength(1);
        expect(result[0].sku).toBe('NEW1');
        expect(result[0].qty).toBe(2);
    });

    test('increases qty and recalculates subtotal for existing sku', () => {
        const list = [{ sku: 'EX1', name: 'Gadget', price: 10, qty: 2, subtotal: 20 }];
        const product = { sku: 'EX1', name: 'Gadget', price: 10, qty: 1, subtotal: 10 };
        const result = mergeList(list, product, 1);
        expect(result).toHaveLength(1);
        expect(result[0].qty).toBe(3);
        expect(result[0].subtotal).toBe(30);
    });
});
