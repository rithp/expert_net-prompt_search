# ExpertNet: Academic Professor Matching System

A sophisticated web application that uses AI to analyze research problem statements and match them with the most suitable academic professors based on their expertise.

## Features

- **AI-Powered Analysis**: Uses Google's Gemini AI to extract research tags from problem statements
- **Dual View Modes**:
  - **Team Mode**: Suggests collaborative teams of professors for complex problems
  - **Individual Mode**: Ranks professors individually by expertise relevance
- **Advanced Matching**: Combines semantic similarity and weighted tag matching
- **Real-time Search**: Fast professor matching with cached embeddings
- **Interactive UI**: Modern, responsive web interface with tab-based navigation

## Technology Stack

### Backend
- **Python Flask**: REST API server
- **MongoDB**: Professor data storage
- **Google Gemini AI**: Problem statement analysis
- **SentenceTransformers**: Text embedding and semantic similarity
- **scikit-learn**: Cosine similarity calculations

### Frontend
- **HTML/CSS/JavaScript**: Responsive web interface
- **Tailwind CSS**: Modern styling framework
- **Font Awesome**: Icon library

## Project Structure

```
ProblemNet/
├── backend/
│   ├── src/
│   │   ├── app.py                 # Flask application factory
│   │   ├── routes/
│   │   │   └── api_routes.py      # API endpoints
│   │   ├── services/
│   │   │   └── problem_service.py # Core ML and AI services
│   │   ├── config/
│   │   │   └── settings.py        # Configuration settings
│   │   └── utils/
│   │       └── rate_limiter.py    # API rate limiting
│   ├── run.py                     # Application entry point
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Docker configuration
├── frontend/
│   ├── index.html                 # Main web interface
│   ├── script.js                  # Frontend JavaScript
│   └── style.css                  # Additional styles
└── logs/                          # Application logs
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- MongoDB
- Google API key for Gemini AI

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   export GEMINI_API_KEY="your_gemini_api_key"
   ```

3. **Run the backend**:
   ```bash
   python run.py
   ```
   The API will be available at `http://localhost:5050`

### Frontend Setup

1. **Start a simple HTTP server**:
   ```bash
   cd frontend
   python3 -m http.server 8000
   ```

2. **Access the application**:
   Open `http://localhost:8000` in your browser

## API Endpoints

- `POST /api/analyze` - Analyze problem statement and find matching professors
- `GET /api/tags` - Get all available research tags
- `GET /api/health` - Health check endpoint

## Usage

1. **Enter your research problem** in the text area
2. **Click "Analyze Problem"** to process your input
3. **Switch between tabs**:
   - **Team**: See collaborative professor teams
   - **Individual**: See individually ranked professors
4. **Explore results**: Click on professor profiles and Google Scholar links

## Key Algorithms

### Problem Analysis
- Uses Gemini AI to extract specific research tags from natural language
- Identifies key academic domains and their importance weights
- Provides explanations of the problem approach

### Professor Matching
- **Semantic Similarity**: Uses SentenceTransformers for text embeddings
- **Weighted Scoring**: Combines tag relevance with domain expertise
- **Rank Calculation**: `(semantic_score^2.1 + weighted_score^2) / 2`
- **Department Weighting**: Adjusts scores based on departmental relevance

### Performance Optimization
- **Embedding Caching**: Pre-computes and caches professor embeddings
- **Batch Processing**: Efficient batch encoding of text data
- **Thread Safety**: Uses RLock for concurrent access

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for intelligent problem analysis
- SentenceTransformers for semantic text understanding
- MongoDB for robust data storage
- The academic community for inspiration and data

Contributions are welcome! Please feel free to submit a Pull Request.
