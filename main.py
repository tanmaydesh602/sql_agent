# main.py
import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import seed, get_schema_string, get_dynamic_schema
from agent import ask

app = FastAPI(title="SQL Agent")

UPLOAD_DIR = "uploaded_dbs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Active DB state
active_db = {
    "path": None,
    "schema": None,
    "name": None,
}

class QueryRequest(BaseModel):
    question: str
    history: list[dict] = []

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/upload")
def upload_db(file: UploadFile = File(...)):
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Only .db files are supported.")

    save_path = os.path.join(UPLOAD_DIR, "active.db")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        schema = get_dynamic_schema(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read database: {e}")

    active_db["path"] = save_path
    active_db["schema"] = schema
    active_db["name"] = file.filename

    return {"message": f"Uploaded {file.filename}", "schema": schema}

@app.post("/query")
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not active_db["path"]:
        raise HTTPException(status_code=400, detail="No database loaded. Please upload a .db file first.")
    result = ask(req.question, req.history, active_db["path"], active_db["schema"])
    return result

@app.get("/schema")
def schema():
    return {"name": active_db["name"], "schema": active_db["schema"]}

@app.post("/reset")
def reset():
    active_db["path"] = "sql_agent.db"
    active_db["schema"] = get_schema_string()
    active_db["name"] = "sql_agent.db (default)"
    return {"message": "Reset to default database."}

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)