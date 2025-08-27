def create_table_in_risingwave(
    table_name: str,
    kafka_broker_address: str,
    kafka_topic: str,
):
    """
    Creates a table with the given name inside RisingWave and connects it to the
    given kafka topic.

    This way, RisingWave automatically ingests messages from Kafa and updates the table
    in real time
    """
    # TODO
    # You can do it here in Python like this
    # https://docs.risingwave.com/python-sdk/intro
    #
    # or you can use a Data Migration tool
    # https://github.com/vajol/python-data-engineering-resources/blob/main/resources/db-migration.md
