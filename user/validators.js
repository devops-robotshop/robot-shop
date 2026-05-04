function validateLogin(body) {
    if (!body || body.name === undefined || body.password === undefined) {
        return { valid: false, message: 'name or password not supplied' };
    }
    return { valid: true };
}

function validateRegister(body) {
    if (!body || body.name === undefined || body.password === undefined || body.email === undefined) {
        return { valid: false, message: 'insufficient data' };
    }
    return { valid: true };
}

module.exports = { validateLogin, validateRegister };
