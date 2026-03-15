const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
    const { limit, offset } = req.query;
    res.json({ users: [] });
});

router.get('/:id', (req, res) => {
    res.json({ id: req.params.id });
});

router.post('/', (req, res) => {
    const { name, email } = req.body;
    res.json({ name, email });
});

router.put('/:id', (req, res) => {
    const { name, email } = req.body;
    res.json({ id: req.params.id, name, email });
});

router.delete('/:id', (req, res) => {
    res.json({ deleted: true });
});

module.exports = router;
