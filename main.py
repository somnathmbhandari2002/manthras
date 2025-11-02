# from fastapi import FastAPI, Form, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse, StreamingResponse
# from pymongo import MongoClient, ReturnDocument
# from bson import ObjectId, Binary
# import base64
# import mimetypes
# from typing import Optional, Dict, Any, List, DefaultDict
# from collections import defaultdict

# # -------------------------------------------------
# # MongoDB Atlas Connection
# # -------------------------------------------------
# MONGO_URL = "mongodb+srv://somnath:somnath@cluster0.izhugny.mongodb.net"
# client = MongoClient(MONGO_URL)
# db = client["devi_mantras_db"]

# mantras_collection = db["mantras"]
# contacts_collection = db["contact_profile"]  # single-document collection

# # -------------------------------------------------
# # FastAPI App Setup
# # -------------------------------------------------
# app = FastAPI(title="Devi Mantras API", version="1.2.0")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # tighten for prod
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -------------------------------------------------
# # Root / Health / Version
# # -------------------------------------------------
# @app.get("/")
# def root():
#     return {"message": "🌺 Devi Mantras API is running with MongoDB Atlas"}

# @app.get("/health")
# def health():
#     try:
#         mantras_collection.estimated_document_count()
#         return {"status": "ok"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"DB error: {e}")

# @app.get("/version")
# def version():
#     return {"version": app.version}

# # -------------------------------------------------
# # Admin Authentication (Predefined)
# # -------------------------------------------------
# ADMIN_USERNAME = "admin"
# ADMIN_PASSWORD = "admin"

# @app.post("/auth/login")
# def login(username: str = Form(...), password: str = Form(...)):
#     if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
#         return {"message": "Login successful"}
#     raise HTTPException(status_code=401, detail="Invalid username or password")

# # -------------------------------------------------
# # Helpers
# # -------------------------------------------------
# ALLOWED_CATEGORIES = [
#     "LALITA DEVI",
#     "TITHINITYA DEVI",
#     "BALA TRIPURA SUNDARI",
#     "KALI",
#     "LAKSHMI",
#     "SARASWATHI",
# ]

# def normalize_category(cat: str) -> str:
#     if not cat:
#         raise HTTPException(status_code=400, detail="Category is required")
#     c = cat.strip().upper()
#     if c not in ALLOWED_CATEGORIES:
#         raise HTTPException(status_code=400, detail=f"Invalid category. Allowed: {', '.join(ALLOWED_CATEGORIES)}")
#     return c

# def guess_mime(filename: Optional[str], default: str) -> str:
#     if not filename:
#         return default
#     mt, _ = mimetypes.guess_type(filename)
#     return mt or default

# def ensure_oid(id_str: str) -> ObjectId:
#     try:
#         return ObjectId(id_str)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid id")

# def safe_pop_media(doc: Dict[str, Any]) -> Dict[str, Any]:
#     for k in ["image", "pdf", "audio"]:
#         if k in doc:
#             doc.pop(k)
#     return doc

# def attach_file_urls(doc: Dict[str, Any]) -> Dict[str, Any]:
#     doc["_id"] = str(doc["_id"])
#     doc["image_url"] = f"/mantras/{doc['_id']}/image" if doc.get("image_filename") else None
#     doc["pdf_url"] = f"/mantras/{doc['_id']}/pdf" if doc.get("pdf_filename") else None
#     doc["audio_url"] = f"/mantras/{doc['_id']}/audio" if doc.get("audio_filename") else None
#     return doc

# # -------------------------------------------------
# # Mantras: Upload (with category)
# # -------------------------------------------------
# @app.post("/mantras/upload")
# async def upload_mantra(
#     mantra_name: str = Form(...),
#     language: str = Form(...),
#     description: str = Form(""),
#     category: str = Form(...),  # NEW
#     image: UploadFile = File(...),
#     pdf: UploadFile = File(...),
#     audio: UploadFile = File(None),
# ):
#     norm_cat = normalize_category(category)

#     image_data = await image.read()
#     pdf_data = await pdf.read()
#     audio_data = await audio.read() if audio else None

#     image_ct = image.content_type or guess_mime(image.filename, "image/jpeg")
#     pdf_ct = pdf.content_type or "application/pdf"
#     audio_ct = audio.content_type if audio else None
#     if audio and not audio_ct:
#         audio_ct = guess_mime(audio.filename, "audio/mpeg")

#     mantra = {
#         "name": mantra_name,
#         "language": language,
#         "description": description,
#         "category": norm_cat,  # store normalized
#         "image": Binary(image_data),
#         "image_filename": image.filename,
#         "image_content_type": image_ct,
#         "pdf": Binary(pdf_data),
#         "pdf_filename": pdf.filename,
#         "pdf_content_type": pdf_ct,
#         "audio": Binary(audio_data) if audio_data else None,
#         "audio_filename": audio.filename if audio else None,
#         "audio_content_type": audio_ct,
#     }
#     result = mantras_collection.insert_one(mantra)
#     return {"message": "Mantra uploaded successfully", "id": str(result.inserted_id)}

# # -------------------------------------------------
# # Mantras: List (optional filters)
# # -------------------------------------------------
# @app.get("/mantras")
# def get_mantras(category: Optional[str] = None, language: Optional[str] = None):
#     query: Dict[str, Any] = {}
#     if category:
#         query["category"] = normalize_category(category)
#     if language:
#         query["language"] = language

#     projection = {"image": 0, "pdf": 0, "audio": 0}
#     mantras = list(mantras_collection.find(query, projection).sort([("_id", -1)]))
#     for m in mantras:
#         attach_file_urls(m)
#     return mantras

# # -------------------------------------------------
# # Mantras: Grouped by category for home sections
# # -------------------------------------------------
# @app.get("/mantras/grouped")
# def get_mantras_grouped():
#     projection = {"image": 0, "pdf": 0, "audio": 0}
#     cursor = mantras_collection.find({}, projection).sort([("category", 1), ("_id", -1)])
#     grouped: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
#     for doc in cursor:
#         attach_file_urls(doc)
#         grouped[doc.get("category", "UNCATEGORIZED")].append(doc)
#     # Ensure all allowed categories appear, even if empty
#     out = {cat: grouped.get(cat, []) for cat in ALLOWED_CATEGORIES}
#     return out

# # -------------------------------------------------
# # Mantras: Single (metadata + URLs)
# # -------------------------------------------------
# @app.get("/mantras/{mantra_id}")
# def get_mantra(mantra_id: str):
#     oid = ensure_oid(mantra_id)
#     mantra = mantras_collection.find_one({"_id": oid})
#     if not mantra:
#         raise HTTPException(status_code=404, detail="Mantra not found")
#     safe_pop_media(mantra)
#     attach_file_urls(mantra)
#     return mantra

# # -------------------------------------------------
# # Mantras: Optional Base64 variant
# # -------------------------------------------------
# @app.get("/mantras/{mantra_id}/base64")
# def get_mantra_base64(mantra_id: str):
#     oid = ensure_oid(mantra_id)
#     mantra = mantras_collection.find_one({"_id": oid})
#     if not mantra:
#         raise HTTPException(status_code=404, detail="Mantra not found")
#     response = {
#         "_id": str(mantra["_id"]),
#         "name": mantra.get("name"),
#         "language": mantra.get("language"),
#         "description": mantra.get("description"),
#         "category": mantra.get("category"),
#         "image": base64.b64encode(bytes(mantra["image"])).decode("utf-8") if mantra.get("image") else None,
#         "image_content_type": mantra.get("image_content_type"),
#         "pdf": base64.b64encode(bytes(mantra["pdf"])).decode("utf-8") if mantra.get("pdf") else None,
#         "pdf_content_type": mantra.get("pdf_content_type"),
#         "audio": base64.b64encode(bytes(mantra["audio"])).decode("utf-8") if mantra.get("audio") else None,
#         "audio_content_type": mantra.get("audio_content_type"),
#     }
#     return response

# # -------------------------------------------------
# # Mantras: File streaming
# # -------------------------------------------------
# def fetch_doc_or_404(oid: ObjectId):
#     doc = mantras_collection.find_one({"_id": oid})
#     if not doc:
#         raise HTTPException(status_code=404, detail="Mantra not found")
#     return doc

# @app.get("/mantras/{mantra_id}/image")
# def get_image(mantra_id: str):
#     oid = ensure_oid(mantra_id)
#     doc = fetch_doc_or_404(oid)
#     img = doc.get("image")
#     if not img:
#         raise HTTPException(status_code=404, detail="Image not found")
#     ct = doc.get("image_content_type") or "image/jpeg"
#     return StreamingResponse(iter([bytes(img)]), media_type=ct)

# @app.get("/mantras/{mantra_id}/pdf")
# def get_pdf(mantra_id: str):
#     oid = ensure_oid(mantra_id)
#     doc = fetch_doc_or_404(oid)
#     pdf = doc.get("pdf")
#     if not pdf:
#         raise HTTPException(status_code=404, detail="PDF not found")
#     ct = doc.get("pdf_content_type") or "application/pdf"
#     return StreamingResponse(iter([bytes(pdf)]), media_type=ct)

# @app.get("/mantras/{mantra_id}/audio")
# def get_audio(mantra_id: str):
#     oid = ensure_oid(mantra_id)
#     doc = fetch_doc_or_404(oid)
#     audio = doc.get("audio")
#     if not audio:
#         raise HTTPException(status_code=404, detail="Audio not found")
#     ct = doc.get("audio_content_type") or "audio/mpeg"
#     return StreamingResponse(iter([bytes(audio)]), media_type=ct)

# # -------------------------------------------------
# # Contact Profile: single-document CRUD
# # -------------------------------------------------
# CONTACT_ID = "contact_profile"

# def default_contact():
#     return {
#         "_id": CONTACT_ID,
#         "phone": "",
#         "email": "",
#         "location": "",
#         "map_embed": "",
#         "hero_image_url": ""
#     }

# @app.get("/contact")
# def get_contact():
#     doc = contacts_collection.find_one({"_id": CONTACT_ID})
#     return doc if doc else default_contact()

# @app.post("/contact")
# def upsert_contact(
#     phone: str = Form(""),
#     email: str = Form(""),
#     location: str = Form(""),
#     map_embed: str = Form(""),
#     hero_image_url: str = Form("")
# ):
#     if email and "@" not in email:
#         raise HTTPException(status_code=400, detail="Invalid email")
#     payload = {
#         "_id": CONTACT_ID,
#         "phone": phone.strip(),
#         "email": email.strip(),
#         "location": location.strip(),
#         "map_embed": map_embed.strip(),
#         "hero_image_url": hero_image_url.strip(),
#     }
#     doc = contacts_collection.find_one_and_update(
#         {"_id": CONTACT_ID},
#         {"$set": payload},
#         upsert=True,
#         return_document=ReturnDocument.AFTER
#     )
#     return {"message": "Contact profile saved", "contact": doc or payload}

# @app.delete("/contact")
# def clear_contact():
#     contacts_collection.delete_one({"_id": CONTACT_ID})
#     return {"message": "Contact profile cleared"}

#---------------------------------------------------------------------------------------------------------------

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pymongo import MongoClient, ReturnDocument
from bson import ObjectId, Binary
import mimetypes
from typing import Optional, Dict, Any
from datetime import datetime
from io import BytesIO
import os

# -------------------------------------------------
# Environment Variables
# -------------------------------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://somnath:somnath@cluster0.izhugny.mongodb.net")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# -------------------------------------------------
# MongoDB Connection
# -------------------------------------------------
client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
db = client["devi_mantras_db"]
mantras_collection = db["mantras"]
events_collection = db["events"]
feedback_collection = db["feedback"]

# Ensure TTL index for feedback (auto-delete after 30 days)
feedback_collection.create_index("created_at", expireAfterSeconds=30*24*60*60)

# -------------------------------------------------
# FastAPI App Setup
# -------------------------------------------------
app = FastAPI(title="Devi Mantras API", version="1.3.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
ALLOWED_CATEGORIES = [
    "LALITA DEVI",
    "TITHINITYA DEVI",
    "BALA TRIPURA SUNDARI",
    "KALI",
    "LAKSHMI",
    "SARASWATHI",
]

def normalize_category(cat: str) -> str:
    if not cat:
        raise HTTPException(status_code=400, detail="Category is required")
    c = cat.strip().upper()
    if c not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Allowed: {', '.join(ALLOWED_CATEGORIES)}")
    return c

def guess_mime(filename: Optional[str], default: str) -> str:
    if not filename:
        return default
    mt, _ = mimetypes.guess_type(filename)
    return mt or default

def ensure_oid(oid_str: str) -> ObjectId:
    try:
        return ObjectId(oid_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

def safe_pop_media(doc: Dict[str, Any]) -> Dict[str, Any]:
    for k in ["image", "pdf", "audio"]:
        doc.pop(k, None)
    return doc

def attach_file_urls(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["_id"] = str(doc["_id"])
    if "image_filename" in doc:
        doc["image_url"] = f"/mantras/{doc['_id']}/image"
    if "pdf_filename" in doc:
        doc["pdf_url"] = f"/mantras/{doc['_id']}/pdf"
    if "audio_filename" in doc:
        doc["audio_url"] = f"/mantras/{doc['_id']}/audio"
    return doc

# -------------------------------------------------
# Root / Health / Version
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "🌺 Devi Mantras API is running with MongoDB Atlas"}

@app.get("/health")
def health():
    try:
        mantras_collection.estimated_document_count()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

@app.get("/version")
def version():
    return {"version": app.version}

# -------------------------------------------------
# Admin Authentication
# -------------------------------------------------
@app.post("/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# -------------------------------------------------
# Mantras: CRUD + List
# -------------------------------------------------
@app.post("/mantras/upload")
async def upload_mantra(
    mantra_name: str = Form(...),
    language: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    image: UploadFile = File(...),
    pdf: UploadFile = File(...),
    audio: UploadFile = File(None),
):
    norm_cat = normalize_category(category)
    image_data = await image.read()
    pdf_data = await pdf.read()
    audio_data = await audio.read() if audio else None

    mantra = {
        "name": mantra_name.strip(),
        "language": language.strip(),
        "description": description.strip(),
        "category": norm_cat,
        "image": Binary(image_data),
        "image_filename": image.filename,
        "image_content_type": image.content_type or guess_mime(image.filename, "image/jpeg"),
        "pdf": Binary(pdf_data),
        "pdf_filename": pdf.filename,
        "pdf_content_type": pdf.content_type or "application/pdf",
        "audio": Binary(audio_data) if audio_data else None,
        "audio_filename": audio.filename if audio else None,
        "audio_content_type": audio.content_type if audio else None,
    }
    result = mantras_collection.insert_one(mantra)
    return {"message": "Mantra uploaded successfully", "id": str(result.inserted_id)}

@app.get("/mantras")
def list_mantras():
    projection = {"image": 0, "pdf": 0, "audio": 0}
    docs = list(mantras_collection.find({}, projection).sort([("_id", -1)]))
    return [attach_file_urls(doc) for doc in docs]

@app.get("/mantras/{mantra_id}")
def get_mantra(mantra_id: str):
    oid = ensure_oid(mantra_id)
    doc = mantras_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Mantra not found")
    return attach_file_urls(safe_pop_media(doc))

@app.get("/mantras/{mantra_id}/image")
def get_mantra_image(mantra_id: str):
    oid = ensure_oid(mantra_id)
    doc = mantras_collection.find_one({"_id": oid})
    if not doc or not doc.get("image"):
        raise HTTPException(status_code=404, detail="Image not found")
    return StreamingResponse(BytesIO(doc["image"]), media_type=doc.get("image_content_type", "image/jpeg"))

@app.get("/mantras/{mantra_id}/pdf")
def get_mantra_pdf(mantra_id: str):
    oid = ensure_oid(mantra_id)
    doc = mantras_collection.find_one({"_id": oid})
    if not doc or not doc.get("pdf"):
        raise HTTPException(status_code=404, detail="PDF not found")
    return StreamingResponse(BytesIO(doc["pdf"]), media_type=doc.get("pdf_content_type", "application/pdf"))

@app.get("/mantras/{mantra_id}/audio")
def get_mantra_audio(mantra_id: str):
    oid = ensure_oid(mantra_id)
    doc = mantras_collection.find_one({"_id": oid})
    if not doc or not doc.get("audio"):
        raise HTTPException(status_code=404, detail="Audio not found")
    return StreamingResponse(BytesIO(doc["audio"]), media_type=doc.get("audio_content_type", "audio/mpeg"))

@app.put("/mantras/{mantra_id}")
async def edit_mantra(
    mantra_id: str,
    mantra_name: str = Form(...),
    language: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    image: UploadFile = File(None),
    pdf: UploadFile = File(None),
    audio: UploadFile = File(None),
):
    oid = ensure_oid(mantra_id)
    update_fields = {
        "name": mantra_name.strip(),
        "language": language.strip(),
        "description": description.strip(),
        "category": normalize_category(category),
    }

    if image:
        img_data = await image.read()
        update_fields.update({
            "image": Binary(img_data),
            "image_filename": image.filename,
            "image_content_type": image.content_type or "image/jpeg",
        })
    if pdf:
        pdf_data = await pdf.read()
        update_fields.update({
            "pdf": Binary(pdf_data),
            "pdf_filename": pdf.filename,
            "pdf_content_type": pdf.content_type or "application/pdf",
        })
    if audio:
        audio_data = await audio.read()
        update_fields.update({
            "audio": Binary(audio_data),
            "audio_filename": audio.filename,
            "audio_content_type": audio.content_type or "audio/mpeg",
        })

    doc = mantras_collection.find_one_and_update(
        {"_id": oid}, {"$set": update_fields}, return_document=ReturnDocument.AFTER
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Mantra not found")
    return {"message": "Mantra updated successfully", "mantra": attach_file_urls(safe_pop_media(doc))}

@app.delete("/mantras/{mantra_id}")
def delete_mantra(mantra_id: str):
    oid = ensure_oid(mantra_id)
    result = mantras_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mantra not found")
    return {"message": "Mantra deleted successfully"}


# -------------------------------------------------
# Events: CRUD
# -------------------------------------------------
@app.post("/events")
async def create_event(
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(None),
    pdf: UploadFile = File(None),
):
    if not name.strip():
        raise HTTPException(status_code=400, detail="Event name is required")

    event = {"name": name.strip(), "description": description.strip()}

    if image:
        img_data = await image.read()
        event.update({
            "image": Binary(img_data),
            "image_filename": image.filename,
            "image_content_type": image.content_type or "image/jpeg",
        })
    if pdf:
        pdf_data = await pdf.read()
        event.update({
            "pdf": Binary(pdf_data),
            "pdf_filename": pdf.filename,
            "pdf_content_type": pdf.content_type or "application/pdf",
        })

    result = events_collection.insert_one(event)
    return {"message": "Event created successfully", "id": str(result.inserted_id)}

@app.get("/events")
def list_events():
    projection = {"image": 0, "pdf": 0}
    events = list(events_collection.find({}, projection).sort([("_id", -1)]))
    for e in events:
        e["_id"] = str(e["_id"])
        e["image_url"] = f"/events/{e['_id']}/image" if e.get("image_filename") else None
        e["pdf_url"] = f"/events/{e['_id']}/pdf" if e.get("pdf_filename") else None
        if not e.get("description") and not e.get("image_filename") and not e.get("pdf_filename"):
            e["status"] = "Upcoming Event"
    return events

@app.get("/events/{event_id}/image")
def get_event_image(event_id: str):
    oid = ensure_oid(event_id)
    event = events_collection.find_one({"_id": oid})
    if not event or not event.get("image"):
        raise HTTPException(status_code=404, detail="Image not found")
    return StreamingResponse(BytesIO(event["image"]), media_type=event.get("image_content_type", "image/jpeg"))

@app.get("/events/{event_id}/pdf")
def get_event_pdf(event_id: str):
    oid = ensure_oid(event_id)
    event = events_collection.find_one({"_id": oid})
    if not event or not event.get("pdf"):
        raise HTTPException(status_code=404, detail="PDF not found")
    return StreamingResponse(BytesIO(event["pdf"]), media_type=event.get("pdf_content_type", "application/pdf"))

@app.put("/events/{event_id}")
async def update_event(
    event_id: str,
    name: str = Form(None),
    description: str = Form(None),
    image: UploadFile = File(None),
    pdf: UploadFile = File(None),
):
    oid = ensure_oid(event_id)
    event = events_collection.find_one({"_id": oid})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = {}
    if name and name.strip():
        update_data["name"] = name.strip()
    if description and description.strip():
        update_data["description"] = description.strip()
    if image:
        img_data = await image.read()
        update_data.update({
            "image": Binary(img_data),
            "image_filename": image.filename,
            "image_content_type": image.content_type or "image/jpeg",
        })
    if pdf:
        pdf_data = await pdf.read()
        update_data.update({
            "pdf": Binary(pdf_data),
            "pdf_filename": pdf.filename,
            "pdf_content_type": pdf.content_type or "application/pdf",
        })

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    events_collection.update_one({"_id": oid}, {"$set": update_data})
    return {"message": "Event updated successfully"}

@app.delete("/events/{event_id}")
def delete_event(event_id: str):
    oid = ensure_oid(event_id)
    result = events_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

# -------------------------------------------------
# Feedback
# -------------------------------------------------
@app.post("/feedback")
def submit_feedback(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
):
    if not message.strip():
        raise HTTPException(status_code=400, detail="Feedback message required")

    feedback_doc = {
        "name": name.strip(),
        "email": email.strip(),
        "message": message.strip(),
        "created_at": datetime.utcnow()
    }
    feedback_collection.insert_one(feedback_doc)
    return {"message": "Feedback submitted successfully"}

@app.get("/feedback")
def view_feedback(username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")
    feedbacks = list(feedback_collection.find({}, {"_id": 0}))
    return feedbacks
