const { formatProduct, validateSku } = require('./helpers');

describe('formatProduct', () => {
    test('returns all fields when product is complete', () => {
        const input = { sku: 'ABC1', name: 'Widget', description: 'A widget', price: 9.99, instock: 1, categories: ['tools'] };
        const result = formatProduct(input);
        expect(result.sku).toBe('ABC1');
        expect(result.name).toBe('Widget');
        expect(result.description).toBe('A widget');
        expect(result.price).toBe(9.99);
        expect(result.instock).toBe(1);
        expect(result.categories).toEqual(['tools']);
    });

    test('fills in defaults for missing fields', () => {
        const result = formatProduct({});
        expect(result.sku).toBe('');
        expect(result.name).toBe('');
        expect(result.description).toBe('');
        expect(result.price).toBe(0);
        expect(result.instock).toBe(0);
        expect(result.categories).toEqual([]);
    });

    test('preserves instock: 0 without replacing with default', () => {
        const result = formatProduct({ instock: 0 });
        expect(result.instock).toBe(0);
    });
});

describe('validateSku', () => {
    test('returns true for a valid sku', () => {
        expect(validateSku('SKU-001')).toBe(true);
    });

    test('returns false for empty string', () => {
        expect(validateSku('')).toBe(false);
    });

    test('returns false for whitespace-only string', () => {
        expect(validateSku('   ')).toBe(false);
    });

    test('returns false for non-string values', () => {
        expect(validateSku(null)).toBe(false);
        expect(validateSku(123)).toBe(false);
        expect(validateSku(undefined)).toBe(false);
    });
});
