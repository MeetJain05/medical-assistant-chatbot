import os
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-001")

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

pc=Pinecone(api_key=PINECONE_API_KEY)
index=pc.Index(PINECONE_INDEX_NAME)

embed_model = GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)

llm=ChatGroq(temperature=0.3,model_name="llama-3.1-8b-instant",groq_api_key=GROQ_API_KEY)


prompt=PromptTemplate.from_template("""
You are a helpful healthcare assistant. Answer the following question ONLY based on the provided context.
If the answer cannot be found in the context, say "I don't have enough information to answer this question based on the available documents."
Do NOT make up information or use general knowledge.
                                    
Question: {question}
                                    
Context: {context}
                                    
Answer:""")

rag_chain=prompt | llm


async def answer_query(query:str,user_role:str):
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] User role: {user_role}")

    embedding=await asyncio.to_thread(embed_model.embed_query,query)
    results=await asyncio.to_thread(index.query, vector=embedding,top_k=5,include_metadata=True)

    print(f"[DEBUG] Total matches from Pinecone: {len(results.get('matches', []))}")
    
    filtered_contexts=[]
    sources=set()

    for match in results["matches"]:
        metadata=match["metadata"]
        doc_role = metadata.get("role")
        print(f"[DEBUG] Match score: {match.get('score', 0):.4f}, Doc role: {doc_role}, Has text: {bool(metadata.get('text'))}")
        
        if doc_role == user_role:
            text_content = metadata.get("text","")
            if text_content:
                filtered_contexts.append(text_content)
                sources.add(metadata.get("source"))
                print(f"[DEBUG] Added context from: {metadata.get('source')}")

    print(f"[DEBUG] Filtered contexts count: {len(filtered_contexts)}")

    if not filtered_contexts:
        return {"answer":"No relevant information found for your role. Please contact an administrator.","sources":[]}
    
    docs_text="\\n\\n".join(filtered_contexts)
    print(f"[DEBUG] Total context length: {len(docs_text)} chars")
    
    final_answer=await asyncio.to_thread(rag_chain.invoke,{"question":query,"context":docs_text})


    return {
        "answer":final_answer.content,
        "sources":list(sources)
    }