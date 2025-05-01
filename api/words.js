const express = require('express');
const router = express.Router();
const { Pool } = require('pg');

// Configure PostgreSQL connection
const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'we_learn_greek',
  password: process.env.DB_PASSWORD || 'postgres',
  port: process.env.DB_PORT || 5432,
});

// Get all words for a user
router.get('/', async (req, res) => {
  try {
    // In a real app, you would get the user ID from the authenticated session
    const userId = req.user?.id || 1; // Default to user ID 1 for development
    
    const result = await pool.query(
      'SELECT * FROM words WHERE user_id = $1 ORDER BY date_added DESC',
      [userId]
    );
    
    // Transform database column names to camelCase for frontend
    const words = result.rows.map(word => ({
      id: word.id,
      greek: word.greek_word,
      pronunciation: word.pronunciation,
      translation: word.translation,
      dateAdded: new Date(word.date_added).toISOString().split('T')[0],
      userId: word.user_id
    }));
    
    res.json(words);
  } catch (error) {
    console.error('Error fetching words:', error);
    res.status(500).json({ error: 'Failed to fetch words' });
  }
});

// Add a new word
router.post('/', async (req, res) => {
  try {
    const { greek, pronunciation, translation } = req.body;
    
    // Validate required fields
    if (!greek || !pronunciation || !translation) {
      return res.status(400).json({ error: 'All fields are required' });
    }
    
    // In a real app, you would get the user ID from the authenticated session
    const userId = req.user?.id || 1; // Default to user ID 1 for development
    
    const result = await pool.query(
      'INSERT INTO words (greek_word, pronunciation, translation, user_id, date_added) VALUES ($1, $2, $3, $4, NOW()) RETURNING *',
      [greek, pronunciation, translation, userId]
    );
    
    const newWord = {
      id: result.rows[0].id,
      greek: result.rows[0].greek_word,
      pronunciation: result.rows[0].pronunciation,
      translation: result.rows[0].translation,
      dateAdded: new Date(result.rows[0].date_added).toISOString().split('T')[0],
      userId: result.rows[0].user_id
    };
    
    res.status(201).json(newWord);
  } catch (error) {
    console.error('Error adding word:', error);
    res.status(500).json({ error: 'Failed to add word' });
  }
});

// Delete a word
router.delete('/:id', async (req, res) => {
  try {
    const wordId = req.params.id;
    
    // In a real app, you would get the user ID from the authenticated session
    const userId = req.user?.id || 1; // Default to user ID 1 for development
    
    // Ensure the word belongs to the user
    const result = await pool.query(
      'DELETE FROM words WHERE id = $1 AND user_id = $2 RETURNING *',
      [wordId, userId]
    );
    
    if (result.rowCount === 0) {
      return res.status(404).json({ error: 'Word not found or not authorized' });
    }
    
    res.json({ message: 'Word deleted successfully' });
  } catch (error) {
    console.error('Error deleting word:', error);
    res.status(500).json({ error: 'Failed to delete word' });
  }
});

// Update a word
router.put('/:id', async (req, res) => {
  try {
    const wordId = req.params.id;
    const { greek, pronunciation, translation } = req.body;
    
    // Validate required fields
    if (!greek || !pronunciation || !translation) {
      return res.status(400).json({ error: 'All fields are required' });
    }
    
    // In a real app, you would get the user ID from the authenticated session
    const userId = req.user?.id || 1; // Default to user ID 1 for development
    
    // Ensure the word belongs to the user
    const result = await pool.query(
      'UPDATE words SET greek_word = $1, pronunciation = $2, translation = $3 WHERE id = $4 AND user_id = $5 RETURNING *',
      [greek, pronunciation, translation, wordId, userId]
    );
    
    if (result.rowCount === 0) {
      return res.status(404).json({ error: 'Word not found or not authorized' });
    }
    
    const updatedWord = {
      id: result.rows[0].id,
      greek: result.rows[0].greek_word,
      pronunciation: result.rows[0].pronunciation,
      translation: result.rows[0].translation,
      dateAdded: new Date(result.rows[0].date_added).toISOString().split('T')[0],
      userId: result.rows[0].user_id
    };
    
    res.json(updatedWord);
  } catch (error) {
    console.error('Error updating word:', error);
    res.status(500).json({ error: 'Failed to update word' });
  }
});

module.exports = router; 