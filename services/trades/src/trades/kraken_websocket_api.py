import json
from typing import List

from loguru import logger
from websocket import WebSocket, create_connection

from trades.trade import Trade


class KrakenWebsocketAPI:
    URL = 'wss://ws.kraken.com/v2'

    def __init__(self, product_ids: List[str]) -> None:
        """Initialize Kraken WebSocket API client.
        
        Args:
            product_ids: List of trading pairs to subscribe to (e.g., ['BTC/USD', 'ETH/USD'])
        """
        self.product_ids = product_ids
        self._ws_client: WebSocket = create_connection(self.URL)
        self._subscribe(product_ids)

    def get_trades(self) -> List[Trade]:
        """Retrieve trades from the WebSocket connection.
        
        Returns:
            List of Trade objects, empty list if no trades or on error
        """
        data: str = self._ws_client.recv()

        if 'heartbeat' in data:
            return []

        try:
            message_data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f'Failed to decode JSON message: {e}')
            return []

        try:
            trades_data = message_data['data']
        except KeyError:
            logger.warning('Message missing "data" field, skipping')
            return []

        trades = [
            Trade.from_kraken_websocket_response(
                product_id=trade['symbol'],
                price=trade['price'],
                quantity=trade['qty'],
                timestamp=trade['timestamp'],
            )
            for trade in trades_data
        ]

        return trades

    def _subscribe(self, product_ids: List[str]) -> None:
        """Subscribe to trade data for specified product IDs.
        
        Args:
            product_ids: List of trading pairs to subscribe to
        """
        subscribe_message = {
            'method': 'subscribe',
            'params': {
                'channel': 'trade',
                'symbol': product_ids,
                'snapshot': False,
            },
        }
        self._ws_client.send(json.dumps(subscribe_message))

        for _ in product_ids:
            self._ws_client.recv()
            self._ws_client.recv()

    def is_done(self) -> bool:
        """Check if WebSocket connection is closed.
        
        Returns:
            Always False as this implementation runs continuously
        """
        return False
    
    def close(self) -> None:
        """Close the WebSocket connection."""
        if hasattr(self, '_ws_client'):
            self._ws_client.close()