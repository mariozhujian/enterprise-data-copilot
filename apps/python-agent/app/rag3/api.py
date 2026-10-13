import logging
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from openai import APIError, APITimeoutError
from psycopg import Error as DatabaseError

from app.rag3.errors import RagError
from app.rag3.loader import MAX_FILE_BYTES