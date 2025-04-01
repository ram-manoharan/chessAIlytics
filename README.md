---
title: ChessAIlytics
emoji: ♟️
colorFrom: "blue"
colorTo: "green"
sdk: streamlit 
sdk_version: 1.41.1
app_file: app.py
pinned: false
---
# ChessAIlytics-  Chess Game Analyzer


A chess game analysis application that uses Stockfish and LLM for chess position and game analysis.

## Features

- Interactive chessboard for  analyzing games
- Stockfish engine integration for position evaluation
- AI model for comprehensive game analysis
- PGN import/export functionality
- Move history and navigation
- Opening identification

## Installation

```bash
# Clone the repository
git clone https://github.com/username/chess-game-analyzer.git
cd chess-game-analyzer

# Install dependencies
pip install -r requirements.txt

# Run the setup script to install Stockfish
python setup.py
```

## Usage

```bash
# Run the Streamlit app
streamlit run app.py
```

## Deployment

This application can be deployed to Hugging Face Spaces. See the [deployment instructions](DEPLOYMENT.md) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
