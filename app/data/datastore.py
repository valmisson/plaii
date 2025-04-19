"""
Database abstraction layer for SQLite operations
"""
import os
from sqlite3 import connect, Error, Row
from typing import Dict, List, Any, Optional, Tuple, Union, ContextManager
from contextlib import contextmanager

from app.config.settings import DB_PATH


class Datastore:
    """
    Database abstraction layer for SQLite operations.
    Provides a simple interface for CRUD operations on SQLite database.
    """
    def __init__(self, table: str):
        """
        Initialize datastore with a specific table name.

        Args:
            table (str): The name of the database table
        """
        self.table = table
        self.connection = None
        self.db_path = DB_PATH

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def get_connection(self) -> ContextManager:
        """
        Context manager for database connections.
        Automatically handles connection creation and cleanup.

        Yields:
            Connection: SQLite connection object
        """
        # Reuse existing connection if available and valid
        if self.connection is not None and self.is_connected():
            yield self.connection
            return

        # Create a new connection
        conn = None
        try:
            conn = connect(database=self.db_path, check_same_thread=False)
            conn.row_factory = Row
            self.connection = conn
            yield conn
        except Error as err:
            print(f'Error connecting to database: {err}')
            raise
        finally:
            # We don't close here as we're reusing connections
            # They'll be closed when disconnect() is explicitly called
            pass

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.connection:
            try:
                self.connection.close()
            except Error as err:
                print(f'Error closing connection: {err}')
            finally:
                self.connection = None

    def is_connected(self) -> bool:
        """
        Check if database connection is active.

        Returns:
            bool: True if connection is active, False otherwise
        """
        if self.connection is None:
            return False
        try:
            # Test if connection is still valid by executing a simple query
            self.connection.cursor().execute('SELECT 1')
            return True
        except Error:
            self.connection = None
            return False

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        Automatically handles commits and rollbacks.

        Yields:
            Connection: SQLite connection object
        """
        with self.get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Error as err:
                conn.rollback()
                print(f'Transaction error: {err}')
                raise

    def execute_query(self, query: str, params: Optional[Union[List, Tuple]] = None):
        """
        Execute an SQL query with optional parameters.

        Args:
            query (str): The SQL query to execute
            params (Optional[List, Tuple]): Query parameters

        Returns:
            cursor: SQLite cursor object

        Raises:
            Error: If there's a database error
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor

    def create_table(self, columns: Dict[str, str]) -> None:
        """
        Create a table if it doesn't exist.

        Args:
            columns (Dict[str, str]): Dictionary of column names and their types
        """
        columns_str = ', '.join([f'{column} {type}' for column, type in columns.items()])

        self.execute_query(
            f'''CREATE TABLE IF NOT EXISTS {self.table} ({columns_str})'''
        )

    def save(self, data: Dict[str, Any]) -> int:
        """
        Insert a new record into the table.

        Args:
            data (Dict[str, Any]): Dictionary of column names and values

        Returns:
            int: ID of the inserted row
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])

        cursor = self.execute_query(
            f'INSERT INTO {self.table} ({columns}) VALUES ({placeholders})',
            tuple(data.values())
        )
        return cursor.lastrowid

    def list(self, column: str = '*', condition: Optional[str] = None, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        Retrieve records from the table.

        Args:
            column (str): The column(s) to retrieve
            condition (Optional[str]): WHERE clause condition with ? placeholders
            params (Optional[List]): Parameters for the WHERE condition

        Returns:
            List[Dict[str, Any]]: List of records as dictionaries
        """
        query = f'SELECT {column} FROM {self.table}'

        if condition:
            query += f' WHERE {condition}'

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or [])
                rows = cursor.fetchall()

                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]

                return items
        except Error as err:
            print(f'Error retrieving data: {err}')
            return []

    def update(self, data: Dict[str, Any], condition: str, condition_params: Optional[List] = None) -> int:
        """
        Update records in the table.

        Args:
            data (Dict[str, Any]): Dictionary of column names and values to update
            condition (str): WHERE clause condition with ? placeholders
            condition_params (Optional[List]): Parameters for the WHERE condition

        Returns:
            int: Number of rows affected
        """
        if not data:
            return 0

        columns = ', '.join([f'{column} = ?' for column in data.keys()])

        values = list(data.values())

        # Add condition params to values if provided
        if condition_params:
            values.extend(condition_params)

        query = f'UPDATE {self.table} SET {columns} WHERE {condition}'

        cursor = self.execute_query(query, values)
        return cursor.rowcount

    def delete(self, condition: str, params: Optional[List] = None) -> int:
        """
        Delete records from the table.

        Args:
            condition (str): WHERE clause condition with ? placeholders
            params (Optional[List]): Parameters for the condition

        Returns:
            int: Number of rows affected
        """
        cursor = self.execute_query(f'DELETE FROM {self.table} WHERE {condition}', params)
        return cursor.rowcount

    def get_single(self, column: str = '*', condition: Optional[str] = None,
                  params: Optional[List] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single record from the table.

        Args:
            column (str): The column(s) to retrieve
            condition (Optional[str]): WHERE clause condition with ? placeholders
            params (Optional[List]): Parameters for the WHERE condition

        Returns:
            Optional[Dict[str, Any]]: Record as dictionary or None if not found
        """
        results = self.list(column, condition, params)
        return results[0] if results else None
