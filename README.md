# Task 1 -----

# Algorithmic Trading: SMA Crossover Strategy

## 📈 Project Overview

This project implements a **Simple Moving Average (SMA) Crossover Trading Strategy** using Python and `yfinance`. It is designed as a **class-based system** to fetch historical stock data, generate trading signals, backtest a strategy, and visualize performance.

The strategy focuses on detecting **golden cross** (bullish) and **death cross** (bearish) signals based on 50-day and 200-day SMA trends.

This project helps in:

* Practicing **Python programming**.
* Understanding **financial data and indicators**.
* Learning **algorithmic trading basics**.
* Visualizing **portfolio equity curves and trading signals**.

---

## 🛠 Features

* Fetch historical stock data via `yfinance`.
* Clean and preprocess stock prices.
* Compute **50-day and 200-day moving averages**.
* Generate trading signals for **buy and sell**.
* Backtest strategy with **portfolio simulation**.
* Summarize **profit, ROI, and trade statistics**.
* Visualization of:

  * Stock prices + SMA lines
  * Buy/Sell trades
  * Portfolio equity curve
  * Trading volume

---

## ⚡ Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/sma-crossover-trading.git
cd sma-crossover-trading

# Install dependencies
pip install pandas numpy yfinance matplotlib
```

---

## 💻 Usage

### 1. Run the SMA Strategy

```python
from sma_crossover import SMA_Crossover

# Initialize strategy
strategy = SMA_Crossover("AAPL", "2018-01-01", "2023-12-31", budget=5000)

# Run full pipeline: fetch → compute → backtest → report
results = strategy.run_all()
```

### 2. Visualize Results

```python
from stock_visualizer import StockVisualizer

# Visualize price + SMA
viz = StockVisualizer(strategy.df, "AAPL")
viz.plot_price_and_sma(short_w=50, long_w=200)

# Plot portfolio equity curve
viz.plot_equity_curve(results['equity_curve'])
```

---

## 📊 Example Output

* **Backtest Report**

```
===== SMA CROSSOVER BACKTEST REPORT =====
Symbol: AAPL
Start: 2018-01-01
End: 2023-12-31
Initial Budget: 5000
Final Cash: 7423.5
Total Profit: 2423.5
ROI (%): 48.47
Trades: 12
Win Rate (%): 66.67
```

* **Equity Curve Plot:** Shows how portfolio value changes over time.
* **Price Chart with SMA:** Shows stock price with short and long SMAs.
* **Volume Plot:** Daily trading volume for insights.

---

## 📝 Notes on yfinance DataFrame

| Column    | Description                                                          |
| --------- | -------------------------------------------------------------------- |
| Open      | Price when the market opened.                                        |
| High      | Highest price during the trading day.                                |
| Low       | Lowest price during the trading day.                                 |
| Close     | Closing price at the end of the trading day.                         |
| Adj Close | Adjusted close (splits/dividends considered). Use this for analysis. |
| Volume    | Number of shares traded that day.                                    |

Each row represents **one trading day**.

---

## 🔔 Important Concepts

* **SMA (Simple Moving Average):** Smooths price data over a fixed period.
* **Golden Cross:** Short-term SMA crosses above long-term SMA → buy signal.
* **Death Cross:** Short-term SMA crosses below long-term SMA → sell signal.
* **Equity Curve:** Tracks portfolio value over time.
* **Backtesting:** Simulates trading strategy on historical data to evaluate performance.

---

## 📚 References

* [yfinance Documentation](https://pypi.org/project/yfinance/)
* [Pandas Documentation](https://pandas.pydata.org/)
* [Investopedia – SMA & Golden Cross](https://www.investopedia.com/terms/s/sma.asp)

---

## 🖼 Visualization

The `StockVisualizer` class can:

* Plot adjusted close prices + SMA lines.
* Mark buy/sell signals (optional feature).
* Show portfolio equity curve.
* Show daily trading volume.

---
---



# Task 2 ------
***

# Samsung Phone Advisor

A FastAPI-powered backend and toolkit for Samsung phone searching, spec comparison, and recommendations. Instantly query detailed specs, compare models, or get the best battery picks—backed by a PostgreSQL database of scraped phone data.

***

## 🚀 Features

- **Interactive API:** Use `/ask` to get phone specs, compare models, or find the best battery under a price.
- **RAG Model Search:** Robust and partially fuzzy searching across your Samsung phones table.
- **Specs Extraction:** Clean normalization from GSMArena and storage in PostgreSQL.
- **LLM Review Agent:** Uses LLM (OpenAI/Groq) models for humanlike model-to-model comparisons and recommendations.
- **Designed for extensibility and learning.**

***

## 📦 Project Structure

```
.
├── _1_models.py    # SQLAlchemy models (Phone table schema)
├── _2_db.py        # Database setup and helpers (PostgreSQL, session, queries)
├── _4_rag.py       # Retrieval and ranking agent (search, best battery, etc)
├── _5_agents.py    # Review/LLM agent interface (OpenAI/Groq)
├── main.py         # FastAPI app exposing /ask
└── (_3_scraper.py)    # (GSMArena/spec scraping utility)
```

***

## 🛠️ Setup & Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/yourusername/samsung-phone-advisor.git
   cd samsung-phone-advisor
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure DB connection:**  
   Set your `DATABASE_URL` environment variable (defaults to local Postgres).
   ```
   export DATABASE_URL=postgresql://postgres:yourpass@localhost:5432/samsung_advisor
   ```

4. **Initialize the schema:**
   ```bash
   python _2_db.py
   ```

5. **Scrape data:**  
   Populate database using `_3_scraper.py`

6. **Set your OpenAI or Groq key (for LLM features):**
   ```
   export GROQ_API_KEY=sk-xxxxxxx
   ```

7. **Start the FastAPI service:**
   ```bash
   uvicorn main:app --reload
   ```

***

## 🎯 Usage

*Interact via the OpenAPI/Swagger UI or directly with HTTP/JSON:*

- API docs: visit [http://localhost:8000/docs](http://localhost:8000/docs)
- Example requests:
  ```json
  POST /ask
  {
    "question": "Specs of Samsung Galaxy S23 Ultra"
  }
  ```
  ```json
  {
    "question": "Compare Samsung Galaxy S24 and Samsung Galaxy S24 Ultra"
  }
  ```
  ```json
  {
    "question": "Best battery under $500"
  }
  ```

**Query types supported:**
- `Specs of <model>`
- `Compare <model A> and <model B>`
- `Best battery under $X`

***

## 🗃️ SQLAlchemy Models

Sample phones table fields:

- id
- model_name
- brand
- release_date
- display
- battery
- camera
- ram
- storage
- price_usd
- source_url
- created_at

***

## 🤖 LLM/Review Agent

- Powered by Groq/OpenAI API (set `GROQ_API_KEY`)
- Uses instructions to produce concise, plain-English comparisons and recommendations.

***

## 📝 FAQ / Tips
- **Production:** Secure your API before web deployment; add environment-specific config and secrets management.

***

***

## ✨ Credits

- GSMArena for public phone specs and data
- FastAPI, SQLAlchemy, OpenAI/Groq
- [Md. Raihan Uddin Sarker], 2025

***
***
