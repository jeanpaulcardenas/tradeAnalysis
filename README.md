# TradeAnalysis

TradeAnalysis is a web application that loads MT4 (MetaTrader 4) trading history reports files (.html) and provides in-depth analysis 
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

![](https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzdicjM1dnFwdWMyOWRuOWUxdzg5bTB6YTZ3YTQ4a2dibXBlZzJ4eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ylmPcsguQ8rBe1NitK/giphy.gif)
![](https://imgur.com/9Wn9rHy.gif)
![](https://imgur.com/lHQ46ZB.gif)
![](https://i.imgur.com/pcURBza.gif)

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
python -m run
```

- Open your browser and go to `http://localhost:8050`
- Upload your MT4 trading report and explore your stats!

---

## Project Structure

```
TradeAnalysis/
    dash_apps.py/                   # All dash apps
        graphs.py                   # Graphs page generation (dash app)
    dash_graph_f/                   # All classes and functions used to create graphs in Dash framework
        income.py                   # all classes returning dash figures with real profit and PIPS and data
    data/                           # All data files (all .pkl .log will be created here)
        statement.txt               # An example MT4 earnings report file
    data_classes/                   # Contains parsing, data creation and metrics classes
        mt4data.py                  # Parsing classes
        random_df_generator.py      # Class generating a dataframe containing all data needed to create a metrics object
        statistics.py               # Metrics class. Obtains metrics and dataframes displayed in dash apps
    config.py                       # global variables
    requirements.txt                # requirements
    run.py                          # running module
...
```

---

## Testing

Basic tests for data parsing and metrics will be added

---

## Contributing

Contributions and suggestions are welcome! Please open an issue or pull request.

---

## License

[//]: # ([MIT License]&#40;LICENSE&#41;)

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
- [ ] Deploy app online
