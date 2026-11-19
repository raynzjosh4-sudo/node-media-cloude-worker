const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const apiRoutes = require('./routes');
const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

const app = express();

// Security and utility middleware
app.use(helmet());
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Root route
app.get('/', (req, res) => {
  res.json({
    message: 'Node.js Backend API is running.',
    docs: '/api/v1/health',
  });
});

// API routes
app.use('/api/v1', apiRoutes);

// Error handlers
app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;

