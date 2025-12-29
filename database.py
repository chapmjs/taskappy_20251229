# database.py
import streamlit as st
import mysql.connector
from mysql.connector import pooling
import pandas as pd
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self):
        self.pool = self._create_pool()
    
    def _create_pool(self):
        """Create connection pool"""
        return pooling.MySQLConnectionPool(
            pool_name="task_pool",
            pool_size=5,
            pool_reset_session=True,
            host=st.secrets["mysql"]["host"],
            database=st.secrets["mysql"]["database"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            port=st.secrets["mysql"]["port"]
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = self.pool.get_connection()
        try:
            yield connection
        finally:
            connection.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results as DataFrame"""
        with self.get_connection() as conn:
            return pd.read_sql(query, conn, params=params)
    
    def execute_update(self, query, params=None):
        """Execute an update/insert query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

# Initialize database manager
@st.cache_resource
def get_db():
    return DatabaseManager()
