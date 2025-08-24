import datetime

from pydantic import BaseModel


class Trade(BaseModel):
    product_id: str
    price: float
    quantity: float
    timestamp: str
    timestamp_ms: int

    def to_dict(self) -> dict:
        return self.model_dump()

    @staticmethod
    def unix_seconds_to_iso_format(timestamp_sec: float) -> str:
        """
        Convert Unix timestamp in seconds to ISO 8601 format string with UTC timezone
        Example: "2025-04-24T11:35:42.856851Z"
        """
        dt = datetime.datetime.fromtimestamp(timestamp_sec, tz=datetime.timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')

    @staticmethod
    def iso_format_to_unix_seconds(iso_format: str) -> float:
        """
        Convert ISO 8601 format string with UTC timezone to Unix timestamp in seconds
        Example: "2025-04-24T11:35:42.856851Z" -> 1714084542.856851
        """
        return datetime.datetime.fromisoformat(iso_format).timestamp()

    @classmethod
    def from_kraken_websocket_response(
        cls,
        product_id: str,
        price: float,
        quantity: float,
        timestamp: str,
    ) -> 'Trade':
        """
        Create a Trade object from the Kraken websocket response
        """
        return cls(
            product_id=product_id,
            price=price,
            quantity=quantity,
            timestamp=timestamp,
            timestamp_ms=int(cls.iso_format_to_unix_seconds(timestamp) * 1000),
        )

    @classmethod
    def from_kraken_rest_api_response(
        cls,
        product_id: str,
        price: float,
        quantity: float,
        timestamp_sec: float,
    ) -> 'Trade':
        """
        Create a Trade object from the Kraken REST API response
        """

        return cls(
            product_id=product_id,
            price=price,
            quantity=quantity,
            timestamp=cls.unix_seconds_to_iso_format(timestamp_sec),
            timestamp_ms=int(timestamp_sec * 1000),
        )