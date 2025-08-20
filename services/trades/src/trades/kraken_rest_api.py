import json
import time

import requests
from loguru import logger

from trades.trade import Trade


class KrakenRestAPI:
    URL = 'https://api.kraken.com/0/public/Trades'

    def __init__(self, product_id: str, last_n_days: int):
        self.product_id = product_id
        self.last_n_days = last_n_days
        self._is_done = False

        # get current timestamp in nanoseconds
        self.since_timestamp_ns = int(
            time.time_ns() - last_n_days * 24 * 60 * 60 * 1000000000
        )

    def get_trades(self) -> list[Trade]:
        """
        Sends a GET request to the Kraken API to get the trades for the given product_id
        and since the given timestamp

        Returns:
            list[Trade]: List of trades for the given product_id and since the given timestamp
        """
        # Step 1. Set the right headers and parameters for the request
        headers = {'Accept': 'application/json'}
        params = {
            'pair': self.product_id,
            'since': self.since_timestamp_ns,
        }

        # Step 2. Send GET request to Kraken API
        try:
            # Send a GET request to the Kraken API
            response = requests.request('GET', self.URL, headers=headers, params=params)

        except requests.exceptions.SSLError as e:
            # If we get an error, we sleep for 10 seconds and early return the function
            logger.error(f'The Kraken API is not reachable. Error: {e}')

            # wait 10 seconds and try again
            # It would be better to make this source stateful and recoverable, so if
            # the container goes down and gets restarted by Kubernetes, it can resume
            # from where it left off.
            # TODO: reimplement this class a stateful Quix Streams data source so we don't
            # have sleep here.
            logger.error('Sleeping for 10 seconds and trying again...')
            time.sleep(10)
            return []

        # Step 3. Parse the output as a dictionary
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse response as json: {e}')
            return []

        try:
            # Get the trades data
            trades = data['result'][self.product_id]
        except KeyError as e:
            logger.error(f'Failed to get trades for pair {self.product_id}: {e}')
            return []

        # Step 4. Transform the trades data into a list of Trade objects
        trades = [
            Trade.from_kraken_rest_api_response(
                product_id=self.product_id,
                price=trade[0],
                quantity=trade[1],
                timestamp_sec=trade[2],
            )
            for trade in trades
        ]

        # update the since_timestamp_ns
        self.since_timestamp_ns = int(float(data['result']['last']))

        # check stopping condition
        if self.since_timestamp_ns > int(time.time_ns() - 1000000000):
            # we got trades until now, so we can stop
            self._is_done = True

        # breakpoint()

        return trades

    def is_done(self) -> bool:
        return self._is_done