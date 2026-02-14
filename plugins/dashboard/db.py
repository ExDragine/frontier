from sqlmodel import create_engine

from utils.database import DATABASE_FILE

engine = create_engine(DATABASE_FILE)
