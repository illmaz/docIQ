
import os
import json
import re
from datetime import datetime
from collections import Counter


import fitz
import psycopg2
from fastapi import FastAPI, HTTPException, UploadFile, File
from sqlalchemy import create_engine, text
from openai import OpenAI
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), max_retries=3)

app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)
pg_conn = psycopg2.connect(DB_URL)


pg_conn.autocommit = True
register_vector(pg_conn)

STOP_WORDS = {
    "i", "a", "an", "the", "and", "or", "but", "in", "on", 
    "at", "to", "for", "of", "with", "is", "it", "this", 
    "that", "was", "are", "be", "have", "had", "he", "she",
    "they", "we", "you", "my", "your", "his", "her", "its"
}

def extract_text(contents: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        doc = fitz.open(stream=contents, filetype="pdf")
        extracted = "\n".join([page.get_text() for page in doc])
        doc.close()
        if not extracted.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. It may be a scanned image.")
        return extracted
    else:
        try:
            return contents.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be a text file or PDF")

def analyze_text(input_text: str) -> dict:
    words = input_text.split()

    if not words:
        raise HTTPException(status_code=400, detail="Input text is empty or contains no valid words")
    
    sentences = input_text.split(".")
    word_count = len(words)
    sentence_count = len([s for s in sentences if s.strip()])
    avg_word_length = round(sum(len(w) for w in words) / len(words), 2)
    unique_words = len(set(w.lower() for w in words))

    
    clean_words = [
        stripped for w in words
        for stripped in [w.lower().strip(".,!?")]
        if stripped and stripped not in STOP_WORDS
    ]


    keyword_counts = Counter(clean_words)
    top_keywords = [word for word, count in keyword_counts.most_common(5)]

    if avg_word_length < 4:
        reading_level = "Simple"
    elif avg_word_length < 5:
        reading_level = "Moderate"
    else:
        reading_level = "Complex"

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "unique_words": unique_words,
        "average_word_length": avg_word_length,
        "top_keywords": top_keywords,
        "reading_level": reading_level
    }

def save_to_db(input_text: str, stats: dict, ai_result: dict = None):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO analyses 
            (original_text, word_count, sentence_count, unique_words, average_word_length, top_keywords, reading_level, ai_analysis)
            VALUES (:original_text, :word_count, :sentence_count, :unique_words, :average_word_length, :top_keywords, :reading_level, :ai_analysis)
            ON CONFLICT (original_text) DO UPDATE SET
                word_count = EXCLUDED.word_count,
                sentence_count = EXCLUDED.sentence_count,
                unique_words = EXCLUDED.unique_words,
                average_word_length = EXCLUDED.average_word_length,
                top_keywords = EXCLUDED.top_keywords,
                reading_level = EXCLUDED.reading_level,
                ai_analysis = EXCLUDED.ai_analysis,
                analyzed_at = CURRENT_TIMESTAMP
        """), {
            "original_text": input_text[:500],
            "word_count": stats["word_count"],
            "sentence_count": stats["sentence_count"],
            "unique_words": stats["unique_words"],
            "average_word_length": stats["average_word_length"],
            "top_keywords": ",".join(stats["top_keywords"]),
            "reading_level": stats["reading_level"],
            "ai_analysis": json.dumps(ai_result) if ai_result else None
        })
        conn.commit()
import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    if overlap >= chunk_size:
        raise ValueError(f"Overlap ({overlap}) must be smaller than chunk_size ({chunk_size})")
    
    # Split into sentences instead of raw characters
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
           
            current_chunk = current_chunk[-overlap:] + " " + sentence
        else:
            current_chunk += " " + sentence
    
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

@app.get("/")
def home():
    return {
        "name": "Text Analyzer API",
        "version": "4.0",
        "status": "running",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/analyze")
def analyze(input_text: str):
    stats = analyze_text(input_text)
    save_to_db(input_text, stats)
    return {
        "original_text": input_text,
        **stats,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saved_to_database": True
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    input_text = extract_text(contents, file.filename)
    stats = analyze_text(input_text)
    save_to_db(input_text, stats)
    return {
        "filename": file.filename,
        **stats,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saved_to_database": True
    }

@app.post("/analyze-ai")
async def analyze_ai(file: UploadFile = File(...)):
    contents = await file.read()
    input_text = extract_text(contents, file.filename)

    chunks = chunk_text(input_text)

    # Safety cap — prevent runaway API calls
    if len(chunks) > 20:
        raise HTTPException(
            status_code=400, 
            detail=f"Document too large — {len(chunks)} chunks exceeds the 20 chunk limit. Try a shorter document."
        )

    chunk_summaries = []

    for i, chunk in enumerate(chunks):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a document analyst. Analyze this section and respond in JSON with:
                    - summary: 1-2 sentence summary of this section
                    - key_points: list of 2-3 key points
                    - sentiment: Positive, Negative or Neutral"""
                },
                {
                    "role": "user",
                    "content": f"Analyze section {i+1}:\n\n{chunk}"
                }
            ]
        )

        # Handle JSON parsing safely
        try:
            chunk_result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            chunk_result = {
                "summary": response.choices[0].message.content[:200],
                "key_points": [],
                "sentiment": "Unknown"
            }
        chunk_summaries.append(chunk_result)

    # Include both summaries AND key_points in synthesis
    synthesis_input = "\n\n".join([
        f"Section {i+1}:\nSummary: {c['summary']}\nKey points: {', '.join(c.get('key_points', []))}"
        for i, c in enumerate(chunk_summaries)
    ])

    final_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are a document analyst. Given summaries of document sections respond in JSON with:
                - summary: 2-3 sentence overall summary
                - sentiment: overall Positive, Negative or Neutral
                - key_insights: 3 most important insights from the entire document
                - action_items: list of action items if any, empty list if none"""
            },
            {
                "role": "user",
                "content": f"Combine these section summaries into a final analysis:\n\n{synthesis_input}"
            }
        ]
    )

    # Handle final JSON parsing safely
    try:
        final_result = json.loads(final_response.choices[0].message.content)
    except json.JSONDecodeError:
        final_result = {
            "summary": final_response.choices[0].message.content[:500],
            "sentiment": "Unknown",
            "key_insights": [],
            "action_items": []
        }

    stats = analyze_text(input_text)
    save_to_db(input_text, stats, final_result)

    return {
        "filename": file.filename,
        "chunks_processed": len(chunks),
        "ai_analysis": final_result,
        "word_count": stats["word_count"],
        "reading_level": stats["reading_level"],
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "saved_to_database": True
    }

@app.get("/history")
def history():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, original_text, word_count, reading_level, analyzed_at 
            FROM analyses 
            ORDER BY analyzed_at DESC
            LIMIT 10
        """))
        rows = result.fetchall()

    analyses = []
    for row in rows:
        analyses.append({
            "id": row[0],
            "original_text": row[1],
            "word_count": row[2],
            "reading_level": row[3],
            "analyzed_at": str(row[4])
        })

    return {
        "total_shown": len(analyses),
        "analyses": analyses
    }

@app.post("/index")
async def index_document(file: UploadFile = File(...)):
    contents = await file.read()
    input_text = extract_text(contents, file.filename)
    
    chunks = chunk_text(input_text)
    
    if len(chunks) > 1500:
        raise HTTPException(
            status_code=400,
            detail=f"Document too large — {len(chunks)} chunks exceeds limit"
        )
    
    BATCH_SIZE = 50
    all_embeddings = []
    
    with pg_conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM document_chunks WHERE document_name = %s",
            (file.filename,)
        )
        
        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            cursor.execute(
                """INSERT INTO document_chunks 
                   (document_name, chunk_index, chunk_text, embedding) 
                   VALUES (%s, %s, %s, %s)""",
                (file.filename, i, chunk, embedding)
            )
    
    return {
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "status": "indexed and ready to query",
        "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/query")
async def query_documents(question: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    question_embedding = response.data[0].embedding
    
    with pg_conn.cursor() as cursor:
        cursor.execute(
            """SELECT document_name, chunk_text, 
               1 - (embedding <=> %s::vector) as similarity
               FROM document_chunks
               WHERE 1 - (embedding <=> %s::vector) > 0.1
               ORDER BY embedding <=> %s::vector
               LIMIT 5""",
            (question_embedding, question_embedding, question_embedding)
        )
        
        results = cursor.fetchall()
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No documents indexed yet or no relevant chunks found."
            )
        
        context = "\n\n".join([
            f"Source: {r[0]}\n{r[1]}" 
            for r in results
        ])

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that answers questions based strictly on the provided context. 
                Always cite which document your answer comes from.
                If the context does not contain enough information to answer, say so clearly.
                Never make up information not present in the context."""
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
    )

    answer = response.choices[0].message.content
    
    sources = list(set([r[0] for r in results]))
    chunks_used = [
        {
            "document": r[0],
            "similarity_score": round(float(r[2]), 4),
            "excerpt": r[1][:200] + "..." if len(r[1]) > 200 else r[1]
        }
        for r in results
    ]
    
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "chunks_used": chunks_used,
        "answered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/history/{id}")
def get_analysis(id: int):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, original_text, word_count, sentence_count, 
                   unique_words, average_word_length, top_keywords, 
                   reading_level, ai_analysis, analyzed_at 
            FROM analyses 
            WHERE id = :id
        """), {"id": id})
        row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    ai_analysis = None
    if row[8]:
        try:
            ai_analysis = json.loads(row[8]) if isinstance(row[8], str) else row[8]
        except json.JSONDecodeError:
            ai_analysis = None
    
    return {
        "id": row[0],
        "original_text": row[1],
        "word_count": row[2],
        "sentence_count": row[3],
        "unique_words": row[4],
        "average_word_length": row[5],
        "top_keywords": row[6],
        "reading_level": row[7],
        "ai_analysis": ai_analysis,
        "analyzed_at": str(row[9])
    }

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    with pg_conn.cursor() as cursor:
        cursor.execute(
            "DELETE FROM document_chunks WHERE document_name = %s",
            (filename,)
        )
    
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM analyses WHERE original_text LIKE :filename"),
            {"filename": f"%{filename}%"}
        )
        conn.commit()
    
    return {
        "filename": filename,
        "status": "deleted",
        "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }