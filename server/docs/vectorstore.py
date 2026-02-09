import os
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncio


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001")
PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION", "3072"))

missing = [
    name
    for name, value in {
        "GOOGLE_API_KEY": GOOGLE_API_KEY,
        "PINECONE_API_KEY": PINECONE_API_KEY,
        "PINECONE_INDEX_NAME": PINECONE_INDEX_NAME,
    }.items()
    if not value
]
if missing:
    raise RuntimeError(
        "Missing required environment variables: " + ", ".join(missing)
    )

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
UPLOAD_DIR = "./uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

pc = Pinecone(api_key=PINECONE_API_KEY)

# Check if index exists, create if not
existing_indexes = [idx.name for idx in pc.list_indexes()]

if PINECONE_INDEX_NAME not in existing_indexes:
    from pinecone import ServerlessSpec
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=PINECONE_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"Created new index: {PINECONE_INDEX_NAME}")
    # Wait for index to be ready
    import time
    while not pc.describe_index(PINECONE_INDEX_NAME).status.ready:
        time.sleep(1)

# Connect to index
index = pc.Index(PINECONE_INDEX_NAME)

async def load_vectorstore(uploaded_files, role: str, doc_id: str):
    embed_model = GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)

    for file in uploaded_files:
        save_path = Path(UPLOAD_DIR) / file.filename
        with open(save_path, "wb") as f:
            f.write(file.file.read())

        print(f"[UPLOAD DEBUG] Loading PDF: {file.filename}")
        loader = PyPDFLoader(str(save_path))
        documents = loader.load()
        print(f"[UPLOAD DEBUG] Loaded {len(documents)} pages")

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(documents)
        print(f"[UPLOAD DEBUG] Split into {len(chunks)} chunks")

        texts = [chunk.page_content for chunk in chunks]
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "text": chunk.page_content,
                "source": file.filename,
                "doc_id": doc_id,
                "role": role,
                "page": chunk.metadata.get("page", 0)
            }
            for i, chunk in enumerate(chunks)
        ]
        
        print(f"[UPLOAD DEBUG] Sample metadata: {metadatas[0] if metadatas else 'None'}")
        print(f"[UPLOAD DEBUG] Role assigned: {role}")

        print(f"Embedding {len(texts)} chunks...")
        # Run embedding in main thread
        embeddings = await asyncio.to_thread(embed_model.embed_documents,texts)
        print(f"[UPLOAD DEBUG] Created {len(embeddings)} embeddings")

        print("Uploading to Pinecone...")
        with tqdm(total=len(embeddings), desc="Upserting to Pinecone") as progress:
            index.upsert(vectors=zip(ids, embeddings, metadatas))
            progress.update(len(embeddings))

        print(f"Upload complete for {file.filename}")
