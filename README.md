# TradeAnalysis

TradeAnalysis is a web application that loads MT4 (MetaTrader 4) trading history reports and provides in-depth analysis 
and interactive data visualizations. It is designed for traders and analysts who want to understand and improve their 
trading performance.

---

## Features

- Upload MT4 trading history reports and parse trades & balances
- Calculate key trading metrics (win rate, net income, expectancy, trade efficiency, and more)
- Visualize trading performance with interactive Dash/Plotly charts
- Analyze max/min price movement between trade open/close times (using TraderMade API) to evaluate trade efficiency
- Filter and group metrics by symbol, order type, day of week, and more

---

## Screenshots

![Alt text](./application/screenshots/trade_analysis_first.png?raw=true "Graphs example 1")
![](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzdicjM1dnFwdWMyOWRuOWUxdzg5bTB6YTZ3YTQ4a2dibXBlZzJ4eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ylmPcsguQ8rBe1NitK/giphy.gif)
![](https://imgur.com/9Wn9rHy.gif)
![](https://imgur.com/lHQ46ZB.gif)

---

## Installation

### Prerequisites

- Python 3.8+
- `pip` (Python package manager)
- MT4 trading history report in HTML format
- (Optional) TraderMade API key for max/min price analysis

### Setup

```bash
# Clone the repository
git clone https://github.com/jeanpaulcardenas/tradeAnalysis.git
cd tradeAnalysis

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (for API keys, etc.)
cp .env.example .env
# Edit .env to add your TraderMade API key
```

---

## Usage

```bash
# Start the Dash web application
python -m application.dash_apps.graphs
```

- Open your browser and go to `http://localhost:8050`
- Upload your MT4 trading report and explore your stats!

---

## Project Structure

```
application/
    constants.py         # Shared constants, dropdown options, color settings
    mt4data.py           # Data parsing and trade/balance model classes
    statistics.py        # Metrics calculation and analysis logic
    dash_apps/
        graphs.py        # Dash app and graph layouts
    dash_graph_f/
        income.py        # Graph generation classes (Scatter, Bar, Sunburst, etc.)
...
```

---

## Testing

Basic tests for data parsing and metrics will be added.  
(To run tests, use `pytest` after writing test files.)

---

## Contributing

Contributions and suggestions are welcome! Please open an issue or pull request.

---

## License

[MIT License](LICENSE)

---

## Author

- Jean Paul Cardenas ([@jeanpaulcardenas](https://github.com/jeanpaulcardenas))

---

## Roadmap / TODO

- [ ] Add database support for user metrics and trade caching
- [ ] Add a dash page displaying tables with valuable metrics information
- [ ] Add a load file feature to load the MT4 file
- [ ] Create a 'generate random data' button to generate random trade files for those who don't possess a MT4 account
- [ ] Improve user interface and error handling
- [ ] Add authentication for multiple users
- [ ] Write unit tests for core modules
- [ ] Deploy app online (Heroku, Render, etc.)
