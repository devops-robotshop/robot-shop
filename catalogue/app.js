const express = require('express');
const bodyParser = require('body-parser');

const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// mongoConnected and collection are injectable for testability
let mongoConnected = false;
let collection = null;

app.get('/health', (req, res) => {
    res.json({ app: 'OK', mongo: mongoConnected });
});

app.get('/products', (req, res) => {
    if (mongoConnected) {
        collection.find({}).toArray().then((products) => {
            res.json(products);
        }).catch((e) => {
            res.status(500).send(e);
        });
    } else {
        res.status(500).send('database not avaiable');
    }
});

app.get('/product/:sku', (req, res) => {
    if (mongoConnected) {
        const delay = process.env.GO_SLOW || 0;
        setTimeout(() => {
            collection.findOne({ sku: req.params.sku }).then((product) => {
                if (product) {
                    res.json(product);
                } else {
                    res.status(404).send('SKU not found');
                }
            }).catch((e) => {
                res.status(500).send(e);
            });
        }, delay);
    } else {
        res.status(500).send('database not available');
    }
});

app.get('/products/:cat', (req, res) => {
    if (mongoConnected) {
        collection.find({ categories: req.params.cat }).sort({ name: 1 }).toArray().then((products) => {
            if (products) {
                res.json(products);
            } else {
                res.status(404).send('No products for ' + req.params.cat);
            }
        }).catch((e) => {
            res.status(500).send(e);
        });
    } else {
        res.status(500).send('database not avaiable');
    }
});

app.get('/categories', (req, res) => {
    if (mongoConnected) {
        collection.distinct('categories').then((categories) => {
            res.json(categories);
        }).catch((e) => {
            res.status(500).send(e);
        });
    } else {
        res.status(500).send('database not available');
    }
});

function setMongo(connected, col) {
    mongoConnected = connected;
    collection = col;
}

module.exports = { app, setMongo };
