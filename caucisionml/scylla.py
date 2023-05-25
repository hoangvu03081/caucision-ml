import pandas as pd
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, ConsistencyLevel
from .config import settings
from toolz import valmap


class Scylla:
    BATCH_SIZE = 100

    TYPE_MAPPINGS = {
        'int64': 'int',
        'float64': 'float'
    }

    TYPE_MAPPER = {
        'int64': int
    }

    def __init__(self):
        self.cluster = Cluster([settings.SCYLLA_HOST])
        self.session = self.cluster.connect(settings.SCYLLA_KEYSPACE)

    def fetch_project_data(self, project_data_id) -> pd.DataFrame:
        rows = self.session.execute(f"SELECT * FROM {project_data_id}").all()
        return pd.DataFrame(rows)

    def save_project_estimation(self, project_estimation_id, df):
        schema = df.dtypes.to_dict()
        mapped_schema = valmap(lambda dtype: self.TYPE_MAPPINGS.get(str(dtype)), schema)
        mapped_schema['user_id'] += ' PRIMARY KEY'
        columns_definition = ', '.join([f'\"{column}\" {dtype}' for column, dtype in mapped_schema.items()])

        table_creation_query = f"CREATE TABLE {project_estimation_id} ({columns_definition})"
        self.session.execute(table_creation_query)
        # TODO: Add error handling (e.g. table already exist) and logging here

        column_names = df.columns.tolist()
        columns = ', '.join(map(lambda column: f"\"{column}\"", column_names))
        placeholder = ', '.join(map(lambda column: "?", column_names))
        insert_query = f"INSERT INTO {project_estimation_id} ({columns}) VALUES ({placeholder})"
        prepared_statement = self.session.prepare(insert_query)

        batch = BatchStatement(consistency_level=ConsistencyLevel.ANY)
        user_id_type = str(df.dtypes['user_id'])
        type_mapper = self.TYPE_MAPPER[user_id_type]

        for i, row in df.iterrows():
            row = row.astype(object)
            row['user_id'] = type_mapper(row['user_id'])

            values = [row[column] for column in column_names]
            batch.add(prepared_statement, values)

            if (i + 1) % self.BATCH_SIZE == 0 or i == len(df.index) - 1:
                self.session.execute(batch)
                batch = BatchStatement(consistency_level=ConsistencyLevel.ANY)

