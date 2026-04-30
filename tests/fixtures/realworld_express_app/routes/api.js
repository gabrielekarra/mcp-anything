const express = require('express');
const router = express.Router();

router.get('/articles', (req, res) => res.json([]));
router.post('/articles', (req, res) => res.status(201).json({}));
router.get('/articles/:slug', (req, res) => res.json({}));
router.put('/articles/:slug', (req, res) => res.json({}));
router.delete('/articles/:slug', (req, res) => res.status(204).end());
router.get('/profiles/:username', (req, res) => res.json({}));
router.post('/users/login', (req, res) => res.json({}));
router.post('/users', (req, res) => res.status(201).json({}));

module.exports = router;
