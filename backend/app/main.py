import json
import os
import shutil
from contextlib import asynccontextmanager
from typing import List

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from helper import process_files, initialize_agent
from utils import init_logging
from config import config
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from index_management import IndexManager


load_dotenv()

logger = init_logging(__name__)

app = FastAPI()


@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)}
    )


@app.get("/")
async def root():
    return {"message": "Welcome to my Ajua demo tool!"}


@app.post("/uploadfiles/")
async def create_upload_files(files: List[UploadFile] = File(...), data: str = Form(...)):
    uploaded_dir = "./uploaded"
    json_data = json.loads(data)
    os.environ["OPENAI_API_KEY"] = json_data["openai_api_key"]
    all_tools = await process_files(files, uploaded_dir)
    initialize_agent(all_tools, app)
    return JSONResponse({"message": "Files processed successfully"})

@app.post("/get_response/")
async def get_response(payload_req: Request):
    payload = await payload_req.json()
    query = payload['query']
    logger.info(f"Received a POST request, query: {query}")
    response = app.state.agent.query(query)
    return JSONResponse(content={"response": response.response})


@app.get("/reset_chat")
async def reset_chat():
    logger.info("Resetting RAG agent...")
    app.state.agent.reset()
    logger.info("RAG agent reset")
    return JSONResponse(content={"message": "Chat agent reset"})


@app.get("/delete_index")
async def delete_index():
    logger.info("Deleting index...")
    res = IndexManager(conn_str=config.connection_str, table_name=config.index_table).delete_index()
    return JSONResponse(content={"message": res})


@app.get("/get_index_length")
async def get_index_length():
    try:
        logger.info("Getting index length...")
        idx_len = IndexManager.get_index_length(config.connection_str, f"data_{config.index_table}")
        logger.info(f"Index length: {idx_len}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting index length: {str(e)}")
    return JSONResponse(content={"index_length": f"{idx_len}"})
