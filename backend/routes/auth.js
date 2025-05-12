// backend/routes/auth.js
const express = require('express');
const router = express.Router();
const db = require('../db');

// Handle POST /api/auth
router.post('/', async (req, res) => {
  const {
    gleanAccount,
    gleanToken,
    accountId,
    consumerKey,
    consumerSecret,
    token,
    tokenSecret,
  } = req.body;

  if (!gleanAccount || !gleanToken || !accountId || !consumerKey || !consumerSecret || !token || !tokenSecret) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  try {
    const sql = `
      INSERT INTO auth_credentials
        (glean_account, glean_token, netsuite_account_id, netsuite_consumer_key, netsuite_consumer_secret, netsuite_token, netsuite_token_secret)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `;
    const values = [gleanAccount, gleanToken, accountId, consumerKey, consumerSecret, token, tokenSecret];

    await db.execute(sql, values);
    res.json({ success: true });
  } catch (err) {
    console.error('DB error:', err);
    res.status(500).json({ error: 'Database insert failed' });
  }
});

module.exports = router;