const express = require('express');
const cors = require('cors');
const wordsRouter = require('./api/words');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// API Routes
app.use('/api/words', wordsRouter);

// ... existing routes ...

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 