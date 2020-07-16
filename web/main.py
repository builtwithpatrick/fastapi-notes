from typing import List
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import urllib

# db connection string
DATABASE_URL = 'sqlite:///./data.db'

# db instance
database = databases.Database(DATABASE_URL)

# create db tables
metadata = sqlalchemy.MetaData()


notes = sqlalchemy.Table(
    "notes", 
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('text', sqlalchemy.String),
    sqlalchemy.Column('done', sqlalchemy.Boolean)
)

# create engine
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}
)

metadata.create_all(engine)

#create models with pydantic : these help define request payload

class NoteIn(BaseModel):
    text: str
    done: bool

class Note(BaseModel):
    id: int
    text: str
    done: bool

# setup fastapi app

app = FastAPI(title='API for notes', version='0.1.0')

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# application startup & shutdown events
@app.on_event('startup')
async def startup():
    await database.connect()

@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()

# create a note
@app.post('/notes/', response_model=Note)
async def create_note(note: NoteIn):
    query = notes.insert().values(text=note.text, done=note.done)
    last_record_id = await database.execute(query)
    return {**note.dict(), 'id': last_record_id}

# update a note
@app.put('/notes/{note_id}', response_model=Note)
async def update_note(note_id: int, note: NoteIn):
    query = notes.update().where(notes.c.id == note_id).values(text=note.text, done=note.done)
    await database.execute(query)
    return {**note.dict(), 'id': note_id}

# read all notes
@app.get('/notes/', response_model=List[Note])
async def read_notes(skip: int = 0, take: int =20):
    query = notes.select().offset(skip).limit(take)
    return await database.fetch_all(query)

# read single note
@app.get('/notes/{note_id}', response_model=Note)
async def read_note(note_id: int):
    query = notes.select().where(notes.c.id == note_id)
    return await database.fetch_one(query)

# delete note
@app.delete('/notes/{note_id}')
async def delete_note(note_id: int):
    query = notes.delete().where(notes.c.id == note.id)
    await database.execute(query)
    return {'message': 'note deleted'}
