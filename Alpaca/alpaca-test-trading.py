from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest
import config

client = TradingClient(config.API_KEY, config.SECRET_KEY, paper=False)
account = dict(client.get_account())
for k, v in account.items():
    print(f"{k:30}{v}")

order_details = MarketOrderRequest(
    symbol = "SPY",
    #qty = 1
    notional = 10,
    side = OrderSide.BUY,
    time_in_force = TimeInForce.DAY
)

order = client.submit_order(order_data=order_details)
trades = TradingStream(config.API_KEY, config.SECRET_KEY, paper=False)

async def trade_status(data):
    print(data)

trades.subscribe_trade_updates(trade_status)
trades.run()