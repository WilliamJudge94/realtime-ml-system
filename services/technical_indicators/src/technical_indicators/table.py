def test_risingwave_connectivity(
    risingwave_host: str = "localhost",
    risingwave_port: int = 4567,
    risingwave_user: str = "root",
    risingwave_password: str = "",
    risingwave_database: str = "dev",
) -> bool:
    """
    Test connectivity to RisingWave and log detailed connection information.
    
    Args:
        risingwave_host: RisingWave host
        risingwave_port: RisingWave port
        risingwave_user: RisingWave username
        risingwave_password: RisingWave password
        risingwave_database: RisingWave database name
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    import psycopg2
    from loguru import logger
    
    logger.info("=== RISINGWAVE CONNECTIVITY TEST ===")
    try:
        logger.info(f"Testing connection to RisingWave at {risingwave_host}:{risingwave_port}")
        
        conn = psycopg2.connect(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
            connect_timeout=10
        )
        
        with conn.cursor() as cur:
            # Test basic connectivity
            cur.execute("SELECT 1;")
            result = cur.fetchone()[0]
            logger.success(f"Basic connectivity test passed: {result}")
            
            # Get server status
            try:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                logger.info(f"RisingWave version: {version}")
            except Exception as e:
                logger.warning(f"Could not get version: {e}")
            
            # Test database access
            try:
                cur.execute("SELECT current_database(), current_user();")
                db, user = cur.fetchone()
                logger.info(f"Connected as user '{user}' to database '{db}'")
            except Exception as e:
                logger.warning(f"Could not get user/database info: {e}")
            
            # Test table listing capability
            try:
                cur.execute("SELECT COUNT(*) FROM information_schema.tables;")
                table_count = cur.fetchone()[0]
                logger.info(f"Database contains {table_count} tables")
            except Exception as e:
                logger.warning(f"Could not count tables: {e}")
        
        conn.close()
        logger.success("RisingWave connectivity test PASSED")
        return True
        
    except psycopg2.OperationalError as e:
        logger.error("RisingWave connectivity test FAILED - Connection error:")
        logger.error(f"  {e}")
        return False
    except Exception as e:
        logger.error("RisingWave connectivity test FAILED - Unexpected error:")
        logger.error(f"  {type(e).__name__}: {e}")
        return False


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
        # Log detailed connection information
        logger.info(f"Attempting to connect to RisingWave:")
        logger.info(f"  Host: {risingwave_host}")
        logger.info(f"  Port: {risingwave_port}")
        logger.info(f"  User: {risingwave_user}")
        logger.info(f"  Database: {risingwave_database}")
        logger.info(f"  Password configured: {'Yes' if risingwave_password else 'No'}")
        
        # Connect to RisingWave using PostgreSQL protocol
        logger.debug("Establishing PostgreSQL connection to RisingWave...")
        conn = psycopg2.connect(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database
        )
        conn.autocommit = True
        logger.success(f"Successfully connected to RisingWave at {risingwave_host}:{risingwave_port}")
        
        with conn.cursor() as cur:
            # Get RisingWave version and status information
            logger.debug("Retrieving RisingWave server information...")
            try:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                logger.info(f"RisingWave version: {version}")
            except Exception as e:
                logger.warning(f"Could not retrieve RisingWave version: {e}")
            
            # Check current database
            try:
                cur.execute("SELECT current_database();")
                current_db = cur.fetchone()[0]
                logger.info(f"Connected to database: {current_db}")
            except Exception as e:
                logger.warning(f"Could not retrieve current database: {e}")
            
            # List existing tables for context
            logger.debug("Checking existing tables in database...")
            try:
                cur.execute("""
                    SELECT table_name, table_type 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                existing_tables = cur.fetchall()
                if existing_tables:
                    logger.info(f"Found {len(existing_tables)} existing tables:")
                    for table_name_existing, table_type in existing_tables:
                        logger.info(f"  - {table_name_existing} ({table_type})")
                else:
                    logger.info("No existing tables found in database")
            except Exception as e:
                logger.warning(f"Could not list existing tables: {e}")
            
            # Check if target table already exists
            logger.debug(f"Checking if table '{table_name}' exists...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            
            table_exists = cur.fetchone()[0]
            logger.info(f"Table '{table_name}' exists: {table_exists}")
            
            if table_exists:
                logger.info(f"Table '{table_name}' already exists in RisingWave")
                
                # Get additional information about the existing table
                try:
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position;
                    """, (table_name,))
                    columns = cur.fetchall()
                    logger.info(f"Table '{table_name}' has {len(columns)} columns:")
                    for col_name, data_type, is_nullable in columns:
                        logger.info(f"  - {col_name}: {data_type} (nullable: {is_nullable})")
                except Exception as e:
                    logger.warning(f"Could not retrieve table schema: {e}")
                
                # Check table row count
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                    row_count = cur.fetchone()[0]
                    logger.info(f"Table '{table_name}' contains {row_count} rows")
                except Exception as e:
                    logger.warning(f"Could not get row count for table '{table_name}': {e}")
                
                return True
            
            # Log table creation details
            logger.info(f"Creating new table '{table_name}' in RisingWave...")
            logger.info(f"Kafka integration details:")
            logger.info(f"  - Broker: {kafka_broker_address}")
            logger.info(f"  - Topic: {kafka_topic}")
            logger.info(f"  - Format: PLAIN ENCODE JSON")
            
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
            
            logger.debug(f"Executing CREATE TABLE statement:")
            logger.debug(create_table_sql)
            
            cur.execute(create_table_sql)
            logger.success(f"Successfully created table '{table_name}' in RisingWave")
            
            # Verify table creation
            logger.debug("Verifying table creation...")
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()
            logger.info(f"Verified: table '{table_name}' created with {len(columns)} columns")
            
            return True
            
    except psycopg2.OperationalError as e:
        logger.error(f"RisingWave connection error for table '{table_name}':")
        logger.error(f"  Error code: {e.pgcode if hasattr(e, 'pgcode') else 'N/A'}")
        logger.error(f"  Error message: {e}")
        logger.error(f"  Connection details: {risingwave_host}:{risingwave_port}/{risingwave_database}")
        return False
    except psycopg2.ProgrammingError as e:
        logger.error(f"RisingWave SQL error creating table '{table_name}':")
        logger.error(f"  Error code: {e.pgcode if hasattr(e, 'pgcode') else 'N/A'}")
        logger.error(f"  Error message: {e}")
        if hasattr(e, 'pgerror') and e.pgerror:
            logger.error(f"  Detailed error: {e.pgerror}")
        return False
    except psycopg2.Error as e:
        logger.error(f"RisingWave database error creating table '{table_name}':")
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error code: {e.pgcode if hasattr(e, 'pgcode') else 'N/A'}")
        logger.error(f"  Error message: {e}")
        if hasattr(e, 'pgerror') and e.pgerror:
            logger.error(f"  Detailed error: {e.pgerror}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating table '{table_name}':")
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error message: {e}")
        import traceback
        logger.error(f"  Stack trace: {traceback.format_exc()}")
        return False
    finally:
        if 'conn' in locals():
            try:
                logger.debug("Closing RisingWave connection...")
                conn.close()
                logger.debug("RisingWave connection closed successfully")
            except Exception as e:
                logger.warning(f"Error closing RisingWave connection: {e}")
