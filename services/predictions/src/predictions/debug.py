import threading

import pandas as pd
from risingwave import OutputFormat

from predictions.risingwave_api import get_risingwave_client

rw = get_risingwave_client(
    host='localhost',
    port=4567,
    user='root',
    password='',
    database='dev',
)


test_df1 = pd.DataFrame(
    {
        'product': ['foo', 'bar'],
        'price': [123.4, 456.7],
    }
)
rw.insert(table_name='test_product', data=test_df1)

# # Fetch data from the test_product table via SQL
# rw.fetch("SELECT * FROM test_product", format=OutputFormat.DATAFRAME)


def subscribe_product_change():
    rw.on_change(
        subscribe_from='test_product',
        schema_name='public',
        handler=lambda x: print(x),
        output_format=OutputFormat.DATAFRAME,
        sub_name='test_product_sub_man',
    )


threading.Thread(target=subscribe_product_change).start()

for _ in range(100):
    rw.insert(table_name='test_product', data=test_df1)
    import time

    time.sleep(1)
