# Create an Application instance with Kafka configs
from typing import Optional

from loguru import logger
from quixstreams import Application

from trades.kraken_rest_api import KrakenRestAPI
from trades.kraken_websocket_api import KrakenWebsocketAPI
from trades.trade import Trade


def run(
    kafka_broker_address: str,
    kafka_topic_name: str,
    # Old way to say an object if of this type or that type
    # kraken_api: Union[KrakenWebsocketAPI, KrakenRestAPI],
    # New way to say an object if of this type or that type
    kraken_api: KrakenWebsocketAPI | KrakenRestAPI,
    kafka_topic_partitions: Optional[int] = 1,
):
    app = Application(
        broker_address=kafka_broker_address,
    )

    # Define a topic "my_topic" with JSON serialization
    topic = app.topic(
        name=kafka_topic_name,
        value_serializer='json',
        # You can use the from quixstreams.models import TopicConfig to configure the topic, if the topic does not exist yet.
        # config=TopicConfig(replication_factor=1, num_partitions=kafka_topic_partitions)
    )

    # Create a Producer instance
    with app.get_producer() as producer:
        while not kraken_api.is_done():
            # 1. Fetch the event from the external API
            events: list[Trade] = kraken_api.get_trades()
            # event = {"id": "1", "text": "Lorem ipsum dolor sit amet"}

            for event in events:
                # 2. Serialize an event using the defined Topic
                message = topic.serialize(key=event.product_id, value=event.to_dict())

                # 3. Produce a message into the Kafka topic
                producer.produce(topic=topic.name, value=message.value, key=message.key)

                # logger.info(f'Produced message to topic {topic.name}')
                logger.info(f'Trade {event.to_dict()} pushed to Kafa')

            # breakpoint()


if __name__ == '__main__':
    from trades.config import config

    # create object that can talk to the Kraken API and get us the trade data in real time
    if config.live_or_historical == 'live':
        logger.info('Using live data from Kraken API')
        api = KrakenWebsocketAPI(product_ids=config.product_ids)

    elif config.live_or_historical == 'historical':
        logger.info('Using historical data from Kraken API')
        api = KrakenRestAPI(
            product_id=config.product_ids[0],
            last_n_days=config.last_n_days,
        )
    else:
        raise ValueError(
            'Invalid value for live_or_historical. Must be "live" or "historical".'
        )

    run(
        kafka_broker_address=config.kafka_broker_address,
        kafka_topic_name=config.kafka_topic_name,
        kraken_api=api,
        # kafka_topic_partitions=len(config.kafka_topic_partitions),
    )