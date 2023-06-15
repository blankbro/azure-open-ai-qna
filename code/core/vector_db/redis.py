import logging
from typing import Any, Callable

from langchain.vectorstores.redis import Redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

logger = logging.getLogger()


class RedisExtended(Redis):
    def __init__(
            self,
            redis_url: str,
            index_name: str,
            embedding_function: Callable,
            **kwargs: Any,
    ):
        super().__init__(redis_url, index_name, embedding_function)

        # Check if index exists
        try:
            self.client.ft("prompt-index").info()
        except:
            # Create Redis Index
            self.create_prompt_index()

        try:
            self.client.ft(self.index_name).info()
        except:
            # Create Redis Index
            self.create_index()

    def create_index(self, prefix="doc", distance_metric: str = "COSINE"):
        content = TextField(name="content")
        metadata = TextField(name="metadata")
        content_vector = VectorField("content_vector",
                                     "HNSW", {
                                         "TYPE": "FLOAT32",
                                         "DIM": 1536,
                                         "DISTANCE_METRIC": distance_metric,
                                         "INITIAL_CAP": 1000,
                                     })
        # Create index
        self.client.ft(self.index_name).create_index(
            fields=[content, metadata, content_vector],
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
        )

    # Prompt management
    def create_prompt_index(self, index_name="prompt-index", prefix="prompt"):
        result = TextField(name="result")
        filename = TextField(name="filename")
        prompt = TextField(name="prompt")
        # Create index
        self.client.ft(index_name).create_index(
            fields=[result, filename, prompt],
            definition=IndexDefinition(prefix=[prefix], index_type=IndexType.HASH)
        )
