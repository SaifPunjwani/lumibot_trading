import requests
from config import ALPACA_CONFIG, FMP_API_KEY
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader

class SwingHigh(Strategy):
    data = []
    order_number = 0

    def initialize(self):
        self.sleeptime = "10S"
        self.sma_period = 14
        self.stop_loss_pct = 0.01
        self.trailing_stop_pct = 0.02
        self.symbols = self.get_best_value_stocks()

    def get_best_value_stocks(self):
        url = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={FMP_API_KEY}"
        response = requests.get(url)
        sp500_stocks = response.json()[:50]
        stock_pe_ratios = []

        for stock in sp500_stocks:
            symbol = stock['symbol']
            try:
                pe_ratio = float(stock['peRatioTTM'])
                if pe_ratio > 0:
                    stock_pe_ratios.append((symbol, pe_ratio))
            except (TypeError, ValueError):
                pass

        stock_pe_ratios.sort(key=lambda x: x[1])
        return [x[0] for x in stock_pe_ratios]

    def on_trading_iteration(self):
        for symbol in self.symbols:
            entry_price = self.get_last_price(symbol)
            position = self.get_position(symbol)
            self.log_message(f"Position for {symbol}: {position}")

            data = self.get_historical_data(symbol, bars=self.sma_period + 1)
            close_prices = data['close'].values
            volume = data['volume'].values

            sma = close_prices[-self.sma_period:].mean()
            current_volume = volume[-1]

            if position:
                current_pnl = (entry_price - position.entry_price) / position.entry_price

                if current_pnl <= -self.stop_loss_pct:
                    self.sell(symbol, position.quantity)
                    self.order_number = 0
                elif current_pnl >= self.trailing_stop_pct:
                    self.sell(symbol, position.quantity)
                    self.order_number = 0

            if len(close_prices) > 3:
                temp = close_prices[-3:]
                last_price = close_prices[-1]
                if temp[-1] > temp[1] > temp[0] and last_price > sma:
                    self.log_message(f"Last 3 prints for {symbol}: {temp}")
                    order = self.create_order(symbol, quantity=10, side="buy")
                    self.submit_order(order)
                    self.order_number += 1
                    if self.order_number == 1:
                        self.log_message(f"Entry price for {symbol}: {temp[-1]}")
                        entry_price = temp[-1]

    def before_market_closes(self):
        for symbol in self.symbols:
            self.sell_all(symbol)

if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = SwingHigh(broker=broker)
    trader = Trader()
    trader.add_strategy(strategy)
    trader.run_all()
