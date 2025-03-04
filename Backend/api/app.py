from fastapi import FastAPI, HTTPException
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from AI_content_generator.contentgen import inference
from Translator.translator import translate
from OCR.generation import ImageAnalyzer
import os
import pytz
import shutil
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from pathlib import Path
from uuid import uuid4
from typing import Optional
from datetime import datetime
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse
from Pdf_Qna.rag import RAGSystem, DocumentProcessor, EmbeddingEngine, LLMEngine
from Voice_Dictation.grammar_correction import ProfessionalResponseGenerator
from Voice_Dictation.speech_Recog import SpeechToText


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    timestamp: str


class StatusResponse(BaseModel):
    status: str
    message: str
    timestamp: str


def get_timestamp():
    return datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")


class InferenceRequest(BaseModel):
    query: str


class TranscriptionResponse(BaseModel):
    transcription: str
    corrected_response: str


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to be translated")
    source_lang: str = Field(..., description="Source language (English or Hindi)")
    target_lang: str = Field(..., description="Target language (English or Hindi)")
    country: str = Field(default="India", description="Country context for translation")

    class Config:
        schema_extra = {
            "example": {
                "text": "Hello, how are you?",
                "source_lang": "English",
                "target_lang": "Hindi",
                "country": "India",
            }
        }


class TranslationResponse(BaseModel):
    status: str
    translated_text: str
    source_lang: str
    target_lang: str
    timestamp: str
    detected_language: Optional[str] = None


app = FastAPI()
# Define allowed origins
origins = [
    "http://localhost:3000",  # If you're using React
    "http://localhost:8000",  # Your FastAPI backend
    "http://127.0.0.1:5501",  # If you're using Live Server
    "http://localhost:5500",  # Live Server alternative URL
    # Add any other origins you need
]

# Add CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/inference")
def run_inference(request: InferenceRequest):
    try:
        result = inference(request.query)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analyzer = ImageAnalyzer(str(file_path))
        result = analyzer.analyze_image()

        os.remove(file_path)

        return {"status": "success", "filename": file.filename, "data": result}

    except Exception as e:
        if "file_path" in locals() and file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/translate/", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    try:
        valid_languages = {"English", "Hindi"}

        source_lang = request.source_lang.title()
        target_lang = request.target_lang.title()

        if source_lang not in valid_languages or target_lang not in valid_languages:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid language combination",
                    "message": "Only English and Hindi are supported",
                    "valid_languages": list(valid_languages),
                },
            )

        if source_lang == target_lang:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid language pair",
                    "message": "Source and target languages must be different",
                },
            )

        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Empty text",
                    "message": "Please provide text to translate",
                },
            )

        translated_text = translate(
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=request.text,
            country=request.country,
        )

        response = TranslationResponse(
            status="success",
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            timestamp=datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S"),
            detected_language=source_lang,
        )

        return response

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail={"error": "Translation error", "message": str(e)}
        )

@app.get("/process-audio/", response_model=TranscriptionResponse)
async def process_audio(
    file: UploadFile = File(...), model_name: Optional[str] = "mixtral-8x7b-32768"
):
    """
    Process audio file and return both transcription and grammar-corrected response.

    Args:
        file: Audio file to process
        model_name: Optional model name for the grammar correction (default: mixtral-8x7b-32768)
    """
    try:
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        speech_recognizer = SpeechToText()

        transcribed_text = speech_recognizer.transcribe(temp_file_path)

        generator = ProfessionalResponseGenerator(model_name=model_name)

        response_data = generator.generate_response(transcribed_text)

        if isinstance(response_data, dict) and "original_text" in response_data:

            if "corrected_text" in response_data:
                corrected_response = response_data["corrected_text"]
            else:
                corrected_response = str(response_data)
        else:
            corrected_response = str(response_data)

        os.remove(temp_file_path)

        return TranscriptionResponse(
            transcription=transcribed_text, corrected_response=corrected_response
        )

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return JSONResponse(
            status_code=500, content={"error": f"An error occurred: {str(e)}"}
        )

@app.get("/correct-text/")
async def correct_text(text: str, model_name: Optional[str] = "mixtral-8x7b-32768"):
    """
    Process text input and return grammar-corrected response.

    Args:
        text: Input text to process
        model_name: Optional model name for the grammar correction
    """
    try:
        generator = ProfessionalResponseGenerator(model_name=model_name)
        response_data = generator.generate_response(text)
        
        print(response_data)
        
        
        if isinstance(response_data, dict) and 'original_text' in response_data:
            if 'corrected_version' in response_data:
                corrected_response = response_data['corrected_version']
                corrected_response = corrected_response[1:len(corrected_response)-1]
            else:
                corrected_response = str(response_data)
        else:
            corrected_response = str(response_data)

        return {"corrected_response": corrected_response}

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"An error occurred: {str(e)}"}
        )


@app.post("/setup", response_model=StatusResponse)
async def setup_rag_system(api_key: str = "orjLf2qy6YnY5oOanmFFzS0u7Z15tUyF"):
    """
    Initialize the RAG system with the specified API key.
    Uses a default API key if none is provided.
    """
    global rag_system

    try:
        rag_system = RAGSystem(api_key=api_key)

        return StatusResponse(
            status="success",
            message="RAG system initialized successfully",
            timestamp=get_timestamp(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing RAG system: {str(e)}")
    

    
@app.get("/answer_constitution", response_model=AnswerResponse)
async def answer_constitution_question(question: str, api_key : str = "orjLf2qy6YnY5oOanmFFzS0u7Z15tUyF"):
    """
    Answer a question related to the Constitution of India.
    """
    rag_system_constitution = RAGSystem(api_key=api_key)
    
    vector_store_dir = r"Pdf_Qna\vectorstore_constitution_of_India"
    try:
        answer = rag_system_constitution.query_from_saved_vectorstore(
        vector_store_dir,
        question
    )
        
        return AnswerResponse(
            question=question,
            answer=answer,
            timestamp=get_timestamp()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/process", response_model=AnswerResponse)
async def process_document_and_question(
    question: str, file: Optional[UploadFile] = File(None)
):
    """
    Process a document (if provided) and answer a question.
    If no document is provided, it will use previously ingested documents.
    """
    global rag_system

    if rag_system is None:
        await setup_rag_system()

    try:
        if file is not None:
            if not file.filename.endswith(".pdf"):
                raise HTTPException(
                    status_code=400, detail="Only PDF files are supported"
                )

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            try:
                with temp_file:
                    shutil.copyfileobj(file.file, temp_file)

                rag_system.ingest_pdf(temp_file.name)

                os.unlink(temp_file.name)
            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e

        answer = rag_system.get_answer(question)

        return AnswerResponse(
            question=question, answer=answer, timestamp=get_timestamp()
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
