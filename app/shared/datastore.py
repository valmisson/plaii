from sqlite3 import connect, Error, Row

class Datastore():
    def __init__(self, table: str):
        self.table = table
        self.connection = None

    def connect(self):
        if self.connection is None:
            try:
                self.connection = connect(database='datastore.db', check_same_thread=False)
                self.connection.row_factory = Row
            except Error as err:
                print(f'Error ao conectar ao datastore: {err}')
                raise

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self):
        """Check if database connection is active"""
        if self.connection is None:
            return False
        try:
            # Test if connection is still valid by executing a simple query
            self.connection.cursor().execute('SELECT 1')
            return True
        except Error:
            self.connection = None
            return False

    def execute_query(self, query: str, params=None):
        try:
            # Ensure we have a valid connection
            if not self.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(query, params or [])
            self.connection.commit()

            return cursor
        except Error as err:
            print(f'Erro ao executar a query: {err}')
            if self.connection:
                self.connection.rollback()
            raise

    def create_table(self, columns):
        columns_str = ', '.join([f'{column} {type}' for column, type in columns.items()])

        self.execute_query(
            f'''CREATE TABLE IF NOT EXISTS {self.table} ({columns_str})'''
        )

    def save(self, data):
        columns = ', '.join(data.keys())
        values = ', '.join(['?' for _ in data])

        self.execute_query(
            f'INSERT INTO {self.table} ({columns}) VALUES ({values})',
            tuple(data.values())
        )

    def list(self, column='*', condition=None):
        query = f'SELECT {column} FROM {self.table}'

        if condition:
            query += f' WHERE {condition}'

        cursor = self.execute_query(query)

        rows = cursor.fetchall()

        columns = [description[0] for description in cursor.description]
        items = [dict(zip(columns, row)) for row in rows]

        return items

    def update(self, data, condition):
        columns = ', '.join([f'{column} = ?' for column in data.keys()])

        values = list(data.values())

        query = f'UPDATE {self.table} SET {columns} WHERE {condition}'

        self.execute_query(query, values)

    def delete(self, condition):
        self.execute_query(f'DELETE FROM {self.table} WHERE {condition}')
