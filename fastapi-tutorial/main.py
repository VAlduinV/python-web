import time
import uvicorn
from fastapi import FastAPI, Path, Query, Depends, HTTPException, Request, File, UploadFile
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ValidationError
from sqlalchemy.orm import Session
from starlette import status
from sqlalchemy import text
from starlette.responses import JSONResponse
import pathlib
from db import get_db, Note
from typing import Optional
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class User(BaseModel):
    name: str
    email: EmailStr
    website: HttpUrl
    age: Optional[int] = Field(None, ge=13, le=90)
    friends: Optional[int] = 0

user = User(name="John", email="jane@gmail.com", website="https://jane.com", age=18, friends=0)
print(user)

# double_user = User(name="Bob", email="bob@gmail.com", website="Invalid url", age=12, friends=0)
# print(double_user)

# @app.get("/api/healthchecker")
# def root():
    # return {"message": "Welcome to FastAPI!"}

@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")



@app.post("/api/healthcheck")
def healthcheck(parameter: str):
    return {
        "Input" : parameter,

        "Output" : ''.join([i * 2 for i in parameter[::-1]])
    }

@app.get("/api/note/new")
async def read_new_notes():
    return {"message": "Return new notes"}

class ResponseNoteModel(BaseModel):
    id: int = Field(default=1, ge=1)
    name: str
    description: str
    done: bool

@app.get("/api/notes")
async def read_notes(skip: int = 0, limit: int = Query(default=10, le=100, ge=10), db: Session = Depends(get_db)) -> list[ResponseNoteModel]:
    notes = db.query(Note).offset(skip).limit(limit).all()
    return notes

@app.get("/api/notes/{note_id}", response_model=ResponseNoteModel)
async def read_note(note_id: int = Path(description="The ID of the note to get", gt=0, le=10),
                    db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

class NoteModel(BaseModel):
    name: str
    description: str
    done: bool

@app.post("/notes")
async def create_note(note: NoteModel, db: Session = Depends(get_db)):
    new_note = Note(name=note.name, description=note.description, done=note.done)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/item/{item_id}")
async def read_item(item_id: int):
    item = {"item_id": item_id, "name": "Foo"}
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

class Item(BaseModel):
    name: Optional[str]
    price: Optional[int]

@app.post("/items")
async def create_item(item: Item):
    if item.name is None:
        raise HTTPException(status_code=400, detail="Name is required")
    return item

@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    return {"message": str(exc.detail)}

@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Invalid input data"}
    )

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

@app.exception_handler(Exception)
def unexpected_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"message": "An unexpected error has occurred"})

@app.post("/items/")
async def create_item(item: Item):
    if item.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")
    return item

class ItemNotFoundError(Exception):
    pass

@app.exception_handler(ItemNotFoundError)
def item_not_found_error_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                        content={"message": "Item not found"})

items = [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"},
    {"id": 3, "name": "Item 3"},
]

def get_item_by_id(item_id: int):
    for item in items:
        if item["id"] == item_id:
            return item
    return None

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    item = get_item_by_id(item_id)
    if item is None:
        raise ItemNotFoundError
    return item

# Проміжне програмне забезпечення (middleware) - це функція, яка є програмним компонентом. Цей компонент знаходиться між двома кінцевими точками: клієнтом та сервером, виконуючи певні дії з даними, що проходять через нього.

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.post("/upload_file/")
async def create_upload_file(file: UploadFile = File()):
    pathlib.Path("uploads").mkdir(exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"file_path": file_path}

if __name__ == "__main__":
    uvicorn.run(
        "fastapi-tutorial.main:app",
        host="localhost",
        port=8090,
        reload=True
    )
