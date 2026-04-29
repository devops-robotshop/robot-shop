const { validateLogin, validateRegister } = require('./validators');

describe('validateLogin', () => {
    test('returns valid for name and password present', () => {
        const result = validateLogin({ name: 'alice', password: 'secret' });
        expect(result.valid).toBe(true);
    });

    test('returns invalid when name is missing', () => {
        const result = validateLogin({ password: 'secret' });
        expect(result.valid).toBe(false);
        expect(result.message).toBeDefined();
    });

    test('returns invalid when password is missing', () => {
        const result = validateLogin({ name: 'alice' });
        expect(result.valid).toBe(false);
        expect(result.message).toBeDefined();
    });

    test('returns invalid for empty body', () => {
        const result = validateLogin({});
        expect(result.valid).toBe(false);
    });

    test('returns invalid for null body', () => {
        const result = validateLogin(null);
        expect(result.valid).toBe(false);
    });
});

describe('validateRegister', () => {
    test('returns valid when name, password and email are all present', () => {
        const result = validateRegister({ name: 'alice', password: 'secret', email: 'alice@example.com' });
        expect(result.valid).toBe(true);
    });

    test('returns invalid when name is missing', () => {
        const result = validateRegister({ password: 'secret', email: 'alice@example.com' });
        expect(result.valid).toBe(false);
        expect(result.message).toBeDefined();
    });

    test('returns invalid when password is missing', () => {
        const result = validateRegister({ name: 'alice', email: 'alice@example.com' });
        expect(result.valid).toBe(false);
        expect(result.message).toBeDefined();
    });

    test('returns invalid when email is missing', () => {
        const result = validateRegister({ name: 'alice', password: 'secret' });
        expect(result.valid).toBe(false);
        expect(result.message).toBeDefined();
    });

    test('returns invalid for empty body', () => {
        const result = validateRegister({});
        expect(result.valid).toBe(false);
    });

    test('returns invalid for null body', () => {
        const result = validateRegister(null);
        expect(result.valid).toBe(false);
    });
});
