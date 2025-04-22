"""
Database abstraction layer for SQLite operations
"""
import os
import threading
import queue
from sqlite3 import connect, Error, Row, Connection
from typing import Dict, List, Any, Optional, Tuple, Union, ContextManager
from contextlib import contextmanager

from app.config.settings import DB_PATH


class ConnectionPool:
    """
    A thread-safe connection pool for SQLite database connections.
    Manages a pool of database connections for reuse across threads.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConnectionPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = DB_PATH
        self.pool = queue.Queue(maxsize=10)  # Max 10 connections
        self.active_connections = 0
        self.lock = threading.RLock()
        self._initialized = True

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self) -> Connection:
        """
        Get a connection from the pool or create a new one if needed.

        Returns:
            Connection: A SQLite connection
        """
        with self.lock:
            try:
                # Try to get a connection from the pool
                connection = self.pool.get(block=False)
                return connection
            except queue.Empty:
                # If the pool is empty and we haven't reached the max, create a new connection
                if self.active_connections < 10:
                    connection = self._create_connection()
                    self.active_connections += 1
                    return connection
                else:
                    # Wait for a connection to become available
                    try:
                        return self.pool.get(block=True, timeout=5)
                    except queue.Empty:
                        raise ConnectionError("Failed to get a database connection after waiting")

    def release_connection(self, connection: Connection) -> None:
        """
        Return a connection to the pool.

        Args:
            connection (Connection): The connection to return
        """
        # Test if connection is valid before returning to pool
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self.pool.put(connection, block=False)
        except (Error, queue.Full):
            # If connection is invalid or pool is full, close it
            self._close_connection(connection)

    def _create_connection(self) -> Connection:
        """
        Create a new SQLite connection.

        Returns:
            Connection: A new SQLite connection
        """
        conn = connect(database=self.db_path, check_same_thread=False)
        conn.row_factory = Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Set busy timeout to prevent "database is locked" errors
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _close_connection(self, connection: Connection) -> None:
        """
        Close a connection and decrement the active count.

        Args:
            connection (Connection): The connection to close
        """
        with self.lock:
            try:
                connection.close()
            except Error:
                pass
            finally:
                self.active_connections = max(0, self.active_connections - 1)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self.lock:
            while True:
                try:
                    conn = self.pool.get(block=False)
                    self._close_connection(conn)
                except queue.Empty:
                    break

            self.active_connections = 0


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
        self.db_path = DB_PATH
        self.connection_pool = ConnectionPool()
        self.lock = threading.RLock()

    @contextmanager
    def get_connection(self) -> ContextManager:
        """
        Context manager for database connections.
        Automatically handles connection acquisition and release.

        Yields:
            Connection: SQLite connection object
        """
        conn = None
        try:
            conn = self.connection_pool.get_connection()
            yield conn
        except Error as err:
            print(f'Error with database connection: {err}')
            raise
        finally:
            if conn:
                self.connection_pool.release_connection(conn)

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
