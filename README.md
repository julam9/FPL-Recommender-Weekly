# Football Team Recommendation System

A comprehensive football team recommendation system that builds optimal lineups based on player performance, budget constraints, and opponent analysis.

## Features

- Position-specific player evaluation
- Budget-aware team optimization
- Opponent strength analysis
- Performance tracking over time
- Streamlit web interface for easy interaction
- Web scraping capabilities for real data acquisition
- Comprehensive test suite for all modules

## System Requirements

- Python 3.9 or higher
- Poetry for dependency management

## Installation

1. Clone this repository
2. Install Poetry if you don't have it already:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Install dependencies using Poetry:
   ```
   poetry install
   ```
4. Activate the Poetry virtual environment:
   ```
   poetry shell
   ```
5. Run the application:
   ```
   streamlit run app.py
   ```

## Project Structure

- `app.py`: Main Streamlit application
- `src/`: Source code directory
  - `budget_calculator.py`: Budget-related calculations
  - `data_manager.py`: Functions to load and manage data
  - `opponent_analyzer.py`: Opponent strength analysis
  - `performance_tracker.py`: Track and analyze team performance
  - `player_evaluation.py`: Player evaluation metrics
  - `team_optimizer.py`: Team optimization algorithms
  - `utils.py`: Utility functions
  - `web_scraper.py`: Web scraping functionality for real data
- `tests/`: Unit tests for all modules
- `run_tests.py`: Script to run all tests
- `data/`: Data files directory

## Configuration

You can adjust various parameters in the Streamlit interface:
- Total budget
- Performance vs. budget weights
- Formation preferences
- Number of gameweeks to analyze

## Data

The system can work with:
- Sample data (included for demonstration)
- Real data acquired through web scraping (requires internet connection)
- Custom data uploaded by the user

## Web Scraping

The system includes functionality to scrape real football data from websites using the Trafilatura library.

## Testing

The system includes a comprehensive test suite that covers all core modules. Run the tests using:

```
python run_tests.py
```

or:

```
pytest tests/
```

The test suite includes:
- Unit tests for budget calculations
- Unit tests for player evaluation algorithms
- Unit tests for team optimization
- Unit tests for opponent analysis
- Unit tests for utility functions
- Mock tests for web scraper

Test coverage includes happy paths and edge cases to ensure the system functions correctly under various conditions.