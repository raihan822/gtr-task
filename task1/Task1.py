# sma_strategy.py
import math
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

class SMA_Crossover:
    def __init__(self, symbol, start_date, end_date, budget=5000.0, short_window=50, long_window=200):
        """
        symbol: ticker string, e.g. "AAPL"
        start_date / end_date: "YYYY-MM-DD"
        budget: initial cash in USD
        short_window: e.g. 50
        long_window: e.g. 200
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.budget = float(budget)
        self.short_w = short_window
        self.long_w = long_window

        # runtime state
        self.df = None
        self.trades = []  # list of dicts with trade info
        self.equity_curve = None

    def fetch_data(self):
        # Download historical data using yfinance; use 'Adj Close'
        df = yf.download(self.symbol, start=self.start_date, end=self.end_date, progress=False)
        if df.empty:
            raise ValueError("No data returned. Check symbol/dates or internet connection.")
        df = df[['Adj Close']].rename(columns={'Adj Close': 'adj_close'})
        df.index = pd.to_datetime(df.index)
        self.df = df

    def clean_and_compute(self):
        df = self.df.copy()
        # Remove duplicate index rows
        df = df[~df.index.duplicated(keep='first')]
        # forward fill NaNs
        df['adj_close'] = df['adj_close'].fillna(method='ffill')

        # compute SMAs
        df[f'sma_{self.short_w}'] = df['adj_close'].rolling(self.short_w).mean()
        df[f'sma_{self.long_w}'] = df['adj_close'].rolling(self.long_w).mean()

        # signal: 1 when short above long, else 0
        df['signal'] = 0
        df.loc[df[f'sma_{self.short_w}'] > df[f'sma_{self.long_w}'], 'signal'] = 1

        # shift signal to find changes: buy on 0 -> 1, sell on 1 -> 0
        df['signal_diff'] = df['signal'].diff().fillna(0)

        self.df = df

    def run_backtest(self):
        if self.df is None:
            raise RuntimeError("No data. Run fetch_data() and clean_and_compute() first.")
        df = self.df.copy()

        cash = self.budget
        shares = 0
        equity = []
        trade_open = False
        trade_entry_price = None
        trade_entry_date = None

        for i, (date, row) in enumerate(df.iterrows()):
            price = row['adj_close']
            sdiff = row['signal_diff']

            # BUY signal (0 -> 1)
            if sdiff > 0:
                # only buy if not already in a trade
                if shares == 0:
                    # compute maximum integer number of shares
                    shares_to_buy = int(math.floor(cash / price))
                    if shares_to_buy > 0:
                        cost = shares_to_buy * price
                        cash -= cost
                        shares = shares_to_buy
                        trade_open = True
                        trade_entry_price = price
                        trade_entry_date = date
                        # record event
                        self.trades.append({
                            'type': 'BUY',
                            'date': date,
                            'price': price,
                            'shares': shares_to_buy,
                            'cash_after': cash
                        })
            # SELL signal (1 -> 0)
            elif sdiff < 0:
                if shares > 0:
                    proceeds = shares * price
                    cash += proceeds
                    # record sell trade and P&L
                    profit = (price - trade_entry_price) * shares
                    self.trades.append({
                        'type': 'SELL',
                        'date': date,
                        'price': price,
                        'shares': shares,
                        'cash_after': cash,
                        'entry_date': trade_entry_date,
                        'entry_price': trade_entry_price,
                        'profit': profit
                    })
                    # reset position
                    shares = 0
                    trade_open = False
                    trade_entry_price = None
                    trade_entry_date = None

            # Equity = cash + shares * current price
            equity_val = cash + shares * price
            equity.append({'date': date, 'equity': equity_val, 'cash': cash, 'shares': shares, 'price': price})

        # force close on last row if position still open
        final_date = df.index[-1]
        final_price = df['adj_close'].iloc[-1]
        if shares > 0:
            proceeds = shares * final_price
            cash += proceeds
            profit = (final_price - trade_entry_price) * shares
            self.trades.append({
                'type': 'SELL (FORCED)',
                'date': final_date,
                'price': final_price,
                'shares': shares,
                'cash_after': cash,
                'entry_date': trade_entry_date,
                'entry_price': trade_entry_price,
                'profit': profit
            })
            shares = 0
            equity_val = cash
            equity.append({'date': final_date, 'equity': equity_val, 'cash': cash, 'shares': shares, 'price': final_price})

        # Save equity curve and trades
        self.equity_curve = pd.DataFrame(equity).set_index('date')
        self.df = df
        self.final_cash = cash

    def report(self):
        # compute summary metrics
        trades_df = pd.DataFrame([t for t in self.trades if t['type'].startswith('BUY') or t['type'].startswith('SELL')])
        # pair buys and sells for performance stats
        buys = [t for t in self.trades if t['type'] == 'BUY']
        sells = [t for t in self.trades if t['type'].startswith('SELL')]
        num_trades = len(sells)
        total_profit = sum([t.get('profit', 0.0) for t in sells])
        roi = (self.final_cash - self.budget) / self.budget * 100.0

        # win rate
        wins = sum(1 for s in sells if s.get('profit', 0) > 0)
        win_rate = (wins / num_trades * 100.0) if num_trades > 0 else None

        summary = {
            'symbol': self.symbol,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_budget': self.budget,
            'final_cash': self.final_cash,
            'total_profit': total_profit,
            'ROI_percent': roi,
            'num_trades_sold': num_trades,
            'win_rate_percent': win_rate
        }

        # print summary
        print("=== BACKTEST SUMMARY ===")
        for k, v in summary.items():
            print(f"{k}: {v}")
        print("\nTrades (chronological):")
        for t in self.trades:
            print(t)

        # also return structured results
        return {
            'summary': summary,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }

    def run_all(self):
        """
        convenience wrapper to fetch, compute, run, and report.
        """
        self.fetch_data()
        self.clean_and_compute()
        self.run_backtest()
        return self.report()

# Example usage:
# strat = SMA_Crossover("AAPL", "2018-01-01", "2023-12-31", budget=5000)
# results = strat.run_all()
# equity = results['equity_curve']
# trades = results['trades']
