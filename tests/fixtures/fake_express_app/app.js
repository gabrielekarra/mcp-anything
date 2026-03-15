const express = require('express');
const app = express();
const userRouter = require('./routes/users');

app.use(express.json());
app.use('/api/users', userRouter);

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.get('/api/products', (req, res) => {
    const { limit, category } = req.query;
    res.json({ products: [] });
});

app.get('/api/products/:id', (req, res) => {
    const id = req.params.id;
    res.json({ id });
});

app.post('/api/products', (req, res) => {
    const { name, price } = req.body;
    res.json({ name, price });
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
