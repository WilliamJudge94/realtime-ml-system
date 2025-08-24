import json
import time
from typing import Optional

import requests
from loguru import logger

from trades.models.trade import Trade


class KrakenRestAPI:
    URL = 'https://api.kraken.com/0/public/Trades'
    RETRY_DELAY_SECONDS = 10
    NANOSECONDS_PER_SECOND = 1_000_000_000
    SECONDS_PER_DAY = 24 * 60 * 60

    def __init__(self, product_id: str, last_n_days: int):
        self.product_id = product_id
        self.last_n_days = last_n_days
        self._is_done = False

        # get current timestamp in nanoseconds
        self.since_timestamp_ns = int(
            time.time_ns() - last_n_days * self.SECONDS_PER_DAY * self.NANOSECONDS_PER_SECOND
        )

    def _make_request(self) -> Optional[requests.Response]:
        """Make HTTP request to Kraken API with proper error handling."""
        headers = {'Accept': 'application/json'}
        params = {
            'pair': self.product_id,
            'since': self.since_timestamp_ns,
        }

        try:
            response = requests.request('GET', self.URL, headers=headers, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as e:
            logger.error(f'SSL error connecting to Kraken API: {e}')
            logger.error(f'Sleeping for {self.RETRY_DELAY_SECONDS} seconds and trying again...')
            time.sleep(self.RETRY_DELAY_SECONDS)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'Request failed: {e}')
            return None

    def _parse_response(self, response: requests.Response) -> Optional[dict]:
        """Parse JSON response from API."""
        try:
            data = json.loads(response.text)
            if 'error' in data and data['error']:
                logger.error(f'API returned error: {data["error"]}')
                return None
            return data
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse response as JSON: {e}')
            return None

    def _extract_trades_data(self, data: dict) -> Optional[list]:
        """Extract trades data from API response."""
        try:
            return data['result'][self.product_id]
        except KeyError as e:
            logger.error(f'Failed to get trades for pair {self.product_id}: {e}')
            return None

    def _convert_to_trade_objects(self, trades_data: list) -> list[Trade]:
        """Convert raw trade data to Trade objects."""
        return [
            Trade.from_kraken_rest_api_response(
                product_id=self.product_id,
                price=trade[0],
                quantity=trade[1],
                timestamp_sec=trade[2],
            )
            for trade in trades_data
        ]

    def _update_timestamp(self, data: dict) -> None:
        """Update the since timestamp for next request."""
        self.since_timestamp_ns = int(float(data['result']['last']))
        
        # check stopping condition
        if self.since_timestamp_ns > int(time.time_ns() - self.NANOSECONDS_PER_SECOND):
            # we got trades until now, so we can stop
            self._is_done = True

    def get_trades(self) -> list[Trade]:
        """
        Sends a GET request to the Kraken API to get the trades for the given product_id
        and since the given timestamp

        Returns:
            list[Trade]: List of trades for the given product_id and since the given timestamp
        """
        # Make API request
        response = self._make_request()
        if response is None:
            return []

        # Parse response
        data = self._parse_response(response)
        if data is None:
            return []

        # Extract trades data
        trades_data = self._extract_trades_data(data)
        if trades_data is None:
            return []

        # Convert to Trade objects
        trades = self._convert_to_trade_objects(trades_data)

        # Update timestamp for next request
        self._update_timestamp(data)

        return trades

    def is_done(self) -> bool:
        return self._is_done