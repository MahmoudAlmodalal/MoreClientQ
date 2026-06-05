from fastapi import FastAPI

app = FastAPI(title="Multi-Tenant AI Assistant Platform")

@app.get("/")
def read_root():
    return {"message": "FastAPI backend placeholder skeleton"}
