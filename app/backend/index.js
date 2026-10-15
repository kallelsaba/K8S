const express = require('express');
const mysql   = require('mysql2/promise');
const cors    = require('cors');

const app  = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

const pool = mysql.createPool({
  host:     process.env.DB_HOST || 'mysql',
  port:     process.env.DB_PORT || 3306,
  user:     process.env.DB_USER || 'appuser',
  password: process.env.DB_PASS || '',
  database: process.env.DB_NAME || 'etudiants_db',
  waitForConnections: true,
  connectionLimit: 10,
});

async function initDB() {
  const conn = await pool.getConnection();
  await conn.execute(`
    CREATE TABLE IF NOT EXISTS etudiants (
      id      INT AUTO_INCREMENT PRIMARY KEY,
      nom     VARCHAR(100) NOT NULL,
      prenom  VARCHAR(100) NOT NULL,
      moyenne DECIMAL(4,2) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);
  conn.release();
  console.log('Base de données initialisée');
}

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/etudiants', async (req, res) => {
  try {
    const [rows] = await pool.execute('SELECT * FROM etudiants ORDER BY created_at DESC');
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/etudiants', async (req, res) => {
  const { nom, prenom, moyenne } = req.body;
  if (!nom || !prenom || moyenne === undefined) {
    return res.status(400).json({ error: 'nom, prenom et moyenne sont requis' });
  }
  try {
    const [result] = await pool.execute(
      'INSERT INTO etudiants (nom, prenom, moyenne) VALUES (?, ?, ?)',
      [nom, prenom, moyenne]
    );
    res.status(201).json({ id: result.insertId, nom, prenom, moyenne });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.delete('/api/etudiants/:id', async (req, res) => {
  try {
    await pool.execute('DELETE FROM etudiants WHERE id = ?', [req.params.id]);
    res.json({ message: 'Étudiant supprimé' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

initDB().then(() => {
  app.listen(PORT, () => console.log(`Backend démarré sur le port ${PORT}`));
}).catch(err => {
  console.error('Erreur init DB:', err);
  process.exit(1);
});
