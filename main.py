import os
from pypdf import PdfReader
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from src.dto.query_dto import SimilarQueriesDto
from src.utils.config import DOCUMENTS_PATH, stop_words
from src.utils.llm import get_llm_model
from src.utils.prompt import get_answer_question_from_content, get_questions_from_content
import re
from sentence_transformers import SentenceTransformer
import chromadb
import uuid
import asyncio


client = chromadb.PersistentClient(path="database")
collection = client.get_or_create_collection(
        name="my_collection",
        metadata={"hnsw:space": "cosine"}
    )

embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


llm = get_llm_model()

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


def clean_content(content: str):
    content = content.strip()  # Remove leading and trailing whitespace
    content = content.replace("\n", " ")  # Remove newlines
    return " ".join(content.split())

def get_pdf_files_in_directory(directory_path):
    all_files = os.listdir(directory_path)
    pdf_files = [f for f in all_files if f.lower().endswith(".pdf")]
    return pdf_files

def extract_questions_from_prompt_result(text):
    text = text.replace("\n", "")
    text = text.replace("`", "")
    questions = re.split(r'\d+\.\s', text)
    # Remove the first empty string if it exists
    if questions and questions[0] == '':
        questions.pop(0)

    return questions

def get_list_questions_from_content(content, nbr_questions=30):
    prompt = get_questions_from_content(content, nbr_questions=nbr_questions, model="mistral")
    result = llm.create_completion(
        prompt,
        stream=False,
        max_tokens=2048,
        stop=stop_words,
        temperature=0,
    )
    result = result["choices"][0]["text"]
    result = result.replace("in the context", "")
    result = result.replace("in the given context", "")
    result = clean_content(result)
    content_questions = extract_questions_from_prompt_result(result)
    return content_questions

async def get_references_for_query(query):
    question_emb = embedding_model.encode([query])
    results = collection.query(
        query_embeddings=[t.tolist() for t in question_emb],
        n_results=3
    )

    references = [(r["document"],r["page"]) for r in results["metadatas"][0]]
    references = sorted(list(set(references)))
    print("references", references)
    return references


@app.get("/")
def read_root():
    return FileResponse(Path("static/index.html"), media_type="text/html")


@app.websocket("/stream_completion")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        question = await websocket.receive_text()
        references = await get_references_for_query(question)
        context = ""
        for reference in references:
            reader = PdfReader(DOCUMENTS_PATH +reference[0])
            page_content = reader.pages[reference[1]].extract_text()
            context += (page_content + "\n")

        prompt = get_answer_question_from_content(context, question, model="mistral")
        stream = llm.create_completion(
            prompt,
            stream=True,
            max_tokens=4096,
            stop=stop_words,
            temperature=0.0,
        )
        result = ""
        for output in stream:
            result += output["choices"][0]["text"]
            await websocket.send_json(
                {"type": "message", "data": output["choices"][0]["text"]}
            )
            await asyncio.sleep(0.00001)  # Small delay to ensure real-time streaming


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Create a path to the folder
    file_path = os.path.join("documents", file.filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    reader = PdfReader(DOCUMENTS_PATH + file.filename)
    number_of_pages = len(reader.pages)
    for i in range(number_of_pages):
        page = reader.pages[i]
        page_content = page.extract_text()
        content = page_content

        page_questions = get_list_questions_from_content(content, nbr_questions=30)
        page_questions_emb = embedding_model.encode(page_questions)

        collection.add(
            embeddings= [t.tolist() for t in page_questions_emb],
            documents=page_questions,
            metadatas=[{"page": i , "document": file.filename} for _ in range(len(page_questions))],
            ids=[str(uuid.uuid4()) for j in range(len(page_questions))]
        )

    return {"filename": file.filename, "path": file_path}

@app.post("/queries")
def list_queries(similarQueriesDto: SimilarQueriesDto):
    question_emb = embedding_model.encode([similarQueriesDto.query])
    queries = collection.query(
        query_embeddings=[t.tolist() for t in question_emb],
        n_results=similarQueriesDto.top_k,
            # where={"metadata_field": "is_equal_to_this"}, # optional filter
            # where_document={"$contains":"search_string"}  # optional filter
    )
    return queries["documents"][0]


@app.get("/documents")
def list_documents():
    documents = get_pdf_files_in_directory(DOCUMENTS_PATH)
    return JSONResponse(content=documents)


@app.delete("/delete-document/{file_name}")
def delete_document(file_name: str):
    file_path = Path("documents") / file_name
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)
        return {"status": "success", "message": f"{file_name} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")
