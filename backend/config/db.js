// backend/db.js
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',           // or the username you set
  password: '',           // use the password you set (empty if you hit enter during setup)
  database: 'glean_netsuite_sync',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

module.exports = pool;