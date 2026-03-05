import uvicorn

def start_server(host="127.0.0.1", port=7311):
    uvicorn.run("intentguard.agent.api:app", host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()
