class TradingProvider:
    def get_price(self, symbol):
        raise NotImplementedError

    def place_order(self, order):
        raise NotImplementedError

    def cancel_order(self, order_id):
        raise NotImplementedError


class BrokerProvider(TradingProvider):
    pass


class MockTradingProvider(TradingProvider):
    def get_price(self, symbol):
        from investments.models import Asset

        return Asset.objects.get(symbol=symbol).current_price

    def place_order(self, order):
        from .services import try_execute_order

        return try_execute_order(order)

    def cancel_order(self, order_id):
        from .services import cancel_order

        return cancel_order(order_id)


class BrokerTradingProvider(BrokerProvider):
    def get_price(self, symbol):
        raise NotImplementedError("Broker price feed requires official broker/CMO integration.")

    def place_order(self, order):
        raise NotImplementedError("Real trading requires licensed broker API documentation and authorization.")

    def cancel_order(self, order_id):
        raise NotImplementedError("Real order cancellation requires licensed broker API documentation and authorization.")
