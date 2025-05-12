const db = require('../config/db');

exports.storeAuthCredentials = async (req, res) => {
  const {
    gleanAccount,
    gleanToken,
    accountId,
    consumerKey,
    consumerSecret,
    token,
    tokenSecret
  } = req.body;

  try {
    const [result] = await db.query(
      `INSERT INTO auth_credentials 
        (glean_account, glean_token, account_id, consumer_key, consumer_secret, token, token_secret)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [gleanAccount, gleanToken, accountId, consumerKey, consumerSecret, token, tokenSecret]
    );

    res.status(200).json({ message: 'Auth credentials saved successfully!', id: result.insertId });
  } catch (err) {
    console.error('DB Insert Error:', err);
    res.status(500).json({ error: 'Failed to store credentials.' });
  }
};