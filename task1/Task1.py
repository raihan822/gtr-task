# Important imports:---
import math
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Main Task:---
class SMA_Crossover:
    def __init__(self, symbol, start_date, end_date, budget=5000.0, short_window=50, long_window=200):
        """
        Simple Moving Average (SMA) crossover strategy.
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.budget = float(budget)
        self.short_w = short_window
        self.long_w = long_window

        self.df = None
        self.trades = []
        self.equity_curve = None
        self.final_cash = None

    def fetch_data(self):
        """
        Fetch historical stock data using yfinance.
        Uses adjusted 'Close' prices (new yfinance default).
        """
        df = yf.download(
            self.symbol,
            start=self.start_date,
            end=self.end_date,
            progress=False,
        )
        if df.empty:
            raise ValueError("No data returned. Check symbol/dates or internet connection.")

        # Modern yfinance returns auto-adjusted 'Close' prices
        if 'Close' not in df.columns:
            raise KeyError("'Close' column not found in downloaded data.")

        df = df[['Close']].rename(columns={'Close': 'adj_close'})
        df.index = pd.to_datetime(df.index)
        df = df[~df.index.duplicated(keep='first')]
        df['adj_close'] = df['adj_close'].ffill()

        self.df = df

    def clean_and_compute(self):
        """
        Clean data and compute moving averages and trading signals.
        """
        df = self.df.copy()

        # Compute SMAs
        df[f'sma_{self.short_w}'] = df['adj_close'].rolling(self.short_w).mean()
        df[f'sma_{self.long_w}'] = df['adj_close'].rolling(self.long_w).mean()

        # Generate trading signals
        df['signal'] = (df[f'sma_{self.short_w}'] > df[f'sma_{self.long_w}']).astype(int)
        df['signal_diff'] = df['signal'].diff().fillna(0)

        self.df = df

    def run_backtest(self):
        """
        Run backtest on the SMA crossover signals.
        """
        df = self.df.copy()
        cash = self.budget
        shares = 0
        trade_entry_price = None
        trade_entry_date = None
        equity = []

        for date, row in df.iterrows():
            price = float(row['adj_close'])
            signal_diff = int(row['signal_diff'])

            # BUY signal
            if signal_diff > 0 and shares == 0:
                shares_to_buy = int(math.floor(cash / price))
                if shares_to_buy > 0:
                    cost = shares_to_buy * price
                    cash -= cost
                    shares = shares_to_buy
                    trade_entry_price = price
                    trade_entry_date = date
                    self.trades.append({
                        'type': 'BUY',
                        'date': date,
                        'price': round(price, 2),
                        'shares': shares,
                        'cash_after': round(cash, 2)
                    })

            # SELL signal
            elif signal_diff < 0 and shares > 0:
                proceeds = shares * price
                cash += proceeds
                profit = (price - trade_entry_price) * shares
                self.trades.append({
                    'type': 'SELL',
                    'date': date,
                    'price': round(price, 2),
                    'shares': shares,
                    'cash_after': round(cash, 2),
                    'entry_date': trade_entry_date,
                    'entry_price': round(trade_entry_price, 2),
                    'profit': round(profit, 2)
                })
                shares = 0
                trade_entry_price = None
                trade_entry_date = None

            # Record daily equity
            equity.append({
                'date': date,
                'equity': cash + shares * price,
                'cash': cash,
                'shares': shares
            })

        # Force close open position at end
        if shares > 0:
            final_date = df.index[-1]
            final_price = float(df['adj_close'].iloc[-1])
            proceeds = shares * final_price
            cash += proceeds
            profit = (final_price - trade_entry_price) * shares
            self.trades.append({
                'type': 'SELL (FORCED)',
                'date': final_date,
                'price': round(final_price, 2),
                'shares': shares,
                'cash_after': round(cash, 2),
                'entry_date': trade_entry_date,
                'entry_price': round(trade_entry_price, 2),
                'profit': round(profit, 2)
            })
            shares = 0
            equity.append({
                'date': final_date,
                'equity': cash,
                'cash': cash,
                'shares': shares
            })

        self.equity_curve = pd.DataFrame(equity).set_index('date')
        self.final_cash = cash

    def report(self):
        """
        Summarize the trading performance.
        """
        sells = [t for t in self.trades if 'SELL' in t['type']]
        total_profit = sum(float(t.get('profit', 0)) for t in sells)
        num_trades = len(sells)
        wins = sum(1 for t in sells if float(t.get('profit', 0)) > 0)
        win_rate = (wins / num_trades * 100) if num_trades else 0
        roi = (self.final_cash - self.budget) / self.budget * 100

        summary = {
            'Symbol': self.symbol,
            'Start': self.start_date,
            'End': self.end_date,
            'Initial Budget': round(self.budget, 2),
            'Final Cash': round(self.final_cash, 2),
            'Total Profit': round(total_profit, 2),
            'ROI (%)': round(roi, 2),
            'Trades': num_trades,
            'Win Rate (%)': round(win_rate, 2)
        }

        print("\n===== SMA CROSSOVER BACKTEST REPORT =====")
        for k, v in summary.items():
            print(f"{k}: {v}")

        print("\nTrades:")
        for t in self.trades:
            print(t)

        return {
            'summary': summary,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }

    def run_all(self):
        """
        Full pipeline: fetch → clean → backtest → report
        """
        self.fetch_data()
        self.clean_and_compute()
        self.run_backtest()
        return self.report()

# Testing:---
# trades = results['trades']
# Example run
strat = SMA_Crossover("AAPL", "2018-01-01", "2023-12-31", budget=5000)
results = strat.run_all()

# Optional: inspect equity curve
equity = results['equity_curve']
print(equity.tail())