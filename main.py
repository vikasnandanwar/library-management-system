from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

MONGODB_URL = "mongodb+srv://<vikas>:<157>@cluster0.mongodb.net/library?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGODB_URL)
db = client.library

from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import List

class Student(BaseModel):
    id: str
    name: str
    email: str
    books_issued: List[str] = []

@app.post("/students", response_model=Student)
async def create_student(student: Student):
    student_doc = await db.students.insert_one(student.dict())
    student.id = str(student_doc.inserted_id)
    return student

@app.get("/students/{student_id}", response_model=Student)
async def get_student(student_id: str):
    student = await db.students.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    student["id"] = str(student.pop("_id"))
    return student

@app.get("/students", response_model=List[Student])
async def get_students():
    students = []
    async for student in db.students.find():
        student["id"] = str(student.pop("_id"))
        students.append(student)
    return students

@app.put("/students/{student_id}", response_model=Student)
async def update_student(student_id: str, student: Student):
    updated_student = await db.students.find_one_and_update({"_id": student_id}, {"$set": student.dict()}, upsert=True)
    if not updated_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    updated_student["id"] = str(updated_student.pop("_id"))
    return updated_student

@app.delete("/students/{student_id}")
async def delete_student(student_id: str):
    deleted_student = await db.students.find_one_and_delete({"_id": student_id})
    if not deleted_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"message": "Student deleted successfully"}

@app.post("/students/{student_id}/issue-book", response_model=Student)
async def issue_book(student_id: str, book_id: str):
    student = await db.students.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    student["books_issued"].append(book_id)
    updated_student = await db.students.find_one_and_update({"_id": student_id}, {"$set": student}, upsert=True)
    updated_student["id"] = str(updated_student.pop("_id"))
    return updated_student

@app.post("/students/{student_id}/return-book", response_model=Student)
async def return_book(student_id: str, book_id: str):
    student = await db.students.find_one({"_id": student_id})
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    if book_id not in student["books_issued"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book not issued to this student")
    student["books_issued"].remove(book_id)
    updated_student = await db.students.find_one_and_update({"_id": student_id}, {"$set": student}, upsert=True)
    updated_student["id"] = str(updated_student.pop("_id"))
    return updated_student