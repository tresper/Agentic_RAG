import os
import shutil
from pathlib import Path
from typing import Optional, List

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, SummaryIndex, Settings
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.objects import ObjectIndex
from llama_index.core.tools import FunctionTool, QueryEngineTool
from llama_index.core.vector_stores import MetadataFilters, FilterCondition
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from utils import init_logging
from config import config
from index_management import IndexManager

logger = init_logging(__name__)


def load_documents(file_path: str):
    """Load documents from the specified file path."""
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    return documents


def create_nodes(documents):
    """Create nodes from loaded documents."""
    splitter = SentenceSplitter(chunk_size=1024)
    nodes = splitter.get_nodes_from_documents(documents)
    return nodes


def create_vector_index(nodes):
    """Create a vector index from nodes."""
    vector_index = VectorStoreIndex(nodes)
    return vector_index


def vector_query(
        query: str,
        vector_index: VectorStoreIndex,
        page_numbers: Optional[List[str]] = None
) -> str:
    """Use to answer questions over a given paper.

    Useful if you have specific questions over the paper.
    Always leave page_numbers as None UNLESS there is a specific page you want to search for.

    Args:
        query (str): the string query to be embedded.
        page_numbers (Optional[List[str]]): Filter by set of pages. Leave as NONE
            if we want to perform a vector search
            over all pages. Otherwise, filter by the set of specified pages.

    """

    page_numbers = page_numbers or []
    metadata_dicts = [{"key": "page_label", "value": p} for p in page_numbers]

    query_engine = vector_index.as_query_engine(
        similarity_top_k=2,
        filters=MetadataFilters.from_dicts(metadata_dicts, condition=FilterCondition.OR)
    )
    response = query_engine.query(query)
    return response


def create_vector_query_tool(name: str, vector_index: VectorStoreIndex):
    """Create a vector query tool."""
    return FunctionTool.from_defaults(
        name=f"vector_tool_{name}",
        fn=lambda query, page_numbers=None: vector_query(query, vector_index, page_numbers)
    )


def create_summary_index(nodes):
    """Create a summary index from nodes."""
    summary_index = SummaryIndex(nodes)
    return summary_index


def create_summary_tool(name: str, summary_index: SummaryIndex):
    """Create a summary tool."""
    summary_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        use_async=True,
    )
    return QueryEngineTool.from_defaults(
        name=f"summary_tool_{name}",
        query_engine=summary_query_engine,
        description=(
            "Use ONLY IF you want to get a holistic summary related to {name} "
        ),
    )


async def process_files(files, uploaded_dir):
    logger.info("Initializing models...")
    # llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
    llm = OpenAI(model="gpt-4", temperature=0)
    embed_model = OpenAIEmbedding(model="text-embedding-3-large")
    Settings.llm = llm
    Settings.embed_model = embed_model
    all_tools = []

    logger.info("Processing files...")
    for file in files:
        path = Path(os.path.join(uploaded_dir, file.filename))
        path.parent.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        with open(path, "wb") as f:
            f.write(contents)

        documents = load_documents(str(path))
        nodes = create_nodes(documents)
        index_manager = IndexManager(conn_str=config.connection_str,
                                     table_name=config.index_table,
                                     embed_dim=config.embed_dim)

        logger.info(f"Creating vector index for {file.filename}")
        vector_index = index_manager.create_index(nodes)

        name = path.stem
        logger.info(f"Creating vector query and summary tools for {file.filename}")
        vector_query_tool = create_vector_query_tool(name, vector_index)
        summary_index = create_summary_index(nodes)
        summary_tool = create_summary_tool(name, summary_index)
        all_tools.append(vector_query_tool)
        all_tools.append(summary_tool)

    shutil.rmtree(uploaded_dir, ignore_errors=True)
    return all_tools


def initialize_agent(all_tools, app):
    obj_index = ObjectIndex.from_objects(
        all_tools,
        index_cls=VectorStoreIndex,
    )

    obj_retriever = obj_index.as_retriever(similarity_top_k=3)

    agent_worker = FunctionCallingAgentWorker.from_tools(
        tool_retriever=obj_retriever,
        system_prompt=""" \
    You are an agent designed to answer queries over a set of given papers.
    Please always use the tools provided to answer a question. Do not rely on prior knowledge.\

    """,
        verbose=False
    )
    app.state.agent = AgentRunner(agent_worker)
