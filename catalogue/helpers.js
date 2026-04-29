function formatProduct(product) {
    return {
        sku:         product.sku         || '',
        name:        product.name        || '',
        description: product.description || '',
        price:       product.price       || 0,
        instock:     product.instock     !== undefined ? product.instock : 0,
        categories:  product.categories  || []
    };
}

function validateSku(sku) {
    return typeof sku === 'string' && sku.trim().length > 0;
}

module.exports = { formatProduct, validateSku };
