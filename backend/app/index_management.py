import os

import psycopg2
import requests as req
from dotenv import load_dotenv
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.vector_stores.postgres import PGVectorStore
from psycopg2.extras import NamedTupleCursor
from sqlalchemy import make_url, text, inspect
import sqlalchemy as db
from sqlalchemy_utils import database_exists, create_database, drop_database

from utils import init_logging

load_dotenv()
logger = init_logging(__name__)


class IndexManager:

    def __init__(self, conn_str, table_name, embed_dim=3072):
        self.conn_str = conn_str
        self.table_name = table_name
        self.embed_dim = embed_dim

    def delete_index(self):
        engine = db.create_engine(self.conn_str)
        inspector = inspect(engine)
        url = make_url(self.conn_str)
        if not database_exists(url):
            return "Database does not exist"
        if f"data_{self.table_name}" not in inspector.get_table_names():
            return "Index table does not exist"
        with engine.connect() as conn:
            conn.exec_driver_sql(f"truncate table data_{self.table_name}")
            conn.commit()
        return "Index deleted"

    def create_index(self, nodes):

        url = make_url(self.conn_str)

        if not database_exists(url):
            create_database(url)

        #self.delete_index(self.conn_str, self.table_name)

        hybrid_vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name=self.table_name,
            embed_dim=self.embed_dim,  # openai embedding dimension
            hybrid_search=True,
            text_search_config="english"
        )

        hybrid_storage_context = StorageContext.from_defaults(
            vector_store=hybrid_vector_store
        )

        hybrid_index = VectorStoreIndex(
            nodes=nodes,
            storage_context=hybrid_storage_context
        )

        return hybrid_index

    @classmethod
    def get_index_length(cls, conn_str, index_table):
        url = make_url(conn_str)
        if not database_exists(url):
            return 0
        engine = db.create_engine(conn_str)
        insp = db.inspect(engine)
        has_table = insp.has_table(index_table)
        if not has_table:
            return 0
        with engine.connect() as conn:
            res = conn.execute(text(f"select count(*) from {index_table}"))
            index_len = res.fetchone()

        return index_len[0]


