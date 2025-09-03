def create_table_in_risingwave(
    table_name: str,
    kafka_broker_address: str,
    kafka_topic: str,
    risingwave_host: str = "localhost",
    risingwave_port: int = 4567,
    risingwave_user: str = "root",
    risingwave_password: str = "",
    risingwave_database: str = "dev",
):
    """
    Creates a table with the given name inside RisingWave and connects it to the
    given kafka topic.

    This way, RisingWave automatically ingests messages from Kafka and updates the table
    in real time.
    
    Args:
        table_name: Name of the table to create
        kafka_broker_address: Kafka broker address (host:port)
        kafka_topic: Kafka topic name
        risingwave_host: RisingWave host
        risingwave_port: RisingWave port
        risingwave_user: RisingWave username
        risingwave_password: RisingWave password
        risingwave_database: RisingWave database name
    
    Returns:
        bool: True if table was created or already exists, False if creation failed
    """
    import psycopg2
    from loguru import logger
    
    try:
        # Connect to RisingWave using PostgreSQL protocol
        conn = psycopg2.connect(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database
        )
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Check if table already exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                logger.info(f"Table '{table_name}' already exists in RisingWave")
                return True
            
            # Create the technical indicators table
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                pair VARCHAR,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume FLOAT,
                window_start_ms BIGINT,
                window_end_ms BIGINT,
                candle_seconds INT,
                sma_7 FLOAT,
                sma_14 FLOAT,
                sma_21 FLOAT,
                sma_60 FLOAT,
                ema_7 FLOAT,
                ema_14 FLOAT,
                ema_21 FLOAT,
                ema_60 FLOAT,
                rsi_7 FLOAT,
                rsi_14 FLOAT,
                rsi_21 FLOAT,
                rsi_60 FLOAT,
                macd_7 FLOAT,
                macdsignal_7 FLOAT,
                macdhist_7 FLOAT,
                obv FLOAT,
                PRIMARY KEY (pair, window_start_ms, window_end_ms)
            ) WITH (
                connector='kafka',
                topic='{kafka_topic}',
                properties.bootstrap.server='{kafka_broker_address}'
            ) FORMAT PLAIN ENCODE JSON;
            """
            
            cur.execute(create_table_sql)
            logger.success(f"Successfully created table '{table_name}' in RisingWave")
            return True
            
    except psycopg2.Error as e:
        logger.error(f"Database error creating table '{table_name}': {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating table '{table_name}': {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
