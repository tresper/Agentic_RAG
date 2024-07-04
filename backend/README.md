# MADS Capstone back-end module with REST API.

**NOTE:**  
    $ pip install -r requirements.txt` to install dependencies  

**STEP 1 Run Postgres in Docker**
# First time, Create and Run Postgres in Docker
    $ docker run -e POSTGRES_PASSWORD=postgres -p 5433:5432 --name agentic_demo_pg pgvector/pgvector:pg16
# If Container is already established
    $ docker start agentic_demo_pg

## Default Postgres parameters
    - **username**: postgres
    - **password**: postgres
    - **host**: localhost
    - **port**: 5433

**STEP 2 Start back-end module**
# `--reload` option will restart the server automatically every time changes in the code are made
    $ cd app  
    $ uvicorn main:app --host 127.0.0.1 --port 8081 --reload

## REST API endpoints

- GET **/** - displays a silly greetings message
- GET **/hello/{name}** - displays a silly **Hello {name}!** message
- POST **/get_response/** - returns response for the query 
- GET **/reset_chat** - resets chat engine
- GET **/delete_index** - clears index
- GET **/get_index_length** - returns index length

**STEP 3 Build and run the back-end module in Docker**
# (run in the root dir)
$ docker build -t agentic_rag_app .
$ docker run -p 8081:8080 ragapi-app`


