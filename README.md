# 🏥 RBAC-based RAG Medical Chatbot

A secure, role-based access control (RBAC) chatbot designed for healthcare platforms, powered by Retrieval-Augmented Generation (RAG) with FastAPI, MongoDB, Pinecone, and LangChain.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## 🧠 Overview

This project is a secure, role-sensitive chatbot that answers medical queries using Large Language Models (LLMs) and vector-based document retrieval. It supports role-based access for **Doctors**, **Nurses**, **Patients**, and **Admins**, ensuring that sensitive medical information is retrieved and displayed based on user privileges.

The system uses Retrieval-Augmented Generation (RAG) to provide accurate, context-aware responses by retrieving relevant information from uploaded medical documents stored in a vector database.

## ✨ Features

- **Role-Based Access Control (RBAC):** Different access levels for Admin, Doctor, Nurse, Patient, and Other roles
- **Secure Authentication:** HTTP Basic Auth with bcrypt password hashing
- **Document Upload:** Admin can upload PDF documents targeted to specific roles
- **Intelligent Chat:** RAG-powered chatbot that retrieves relevant medical information
- **Vector Search:** Uses Pinecone for efficient document retrieval
- **Modular Architecture:** Clean separation of concerns with FastAPI backend
- **Web Interface:** Streamlit-based client for easy interaction
- **Health Check:** Built-in health endpoint for monitoring

## ⚙️ Tech Stack

- **Backend:** FastAPI (Python web framework)
- **Database:** MongoDB Atlas (user management)
- **Vector Database:** Pinecone (document embeddings and retrieval)
- **LLM:** Groq API with LLaMA-3 model
- **Embeddings:** Google Generative AI Embeddings
- **Authentication:** HTTP Basic Auth + bcrypt
- **Frontend:** Streamlit (Python web app framework)
- **Document Processing:** LangChain (PDF loading and text splitting)
- **Environment Management:** python-dotenv

## 🏗️ Architecture

### Application Flow

![Application Flow](./assets/applicationFlow.png)

### Core Modules

![Core Modules](./assets/coreModules.png)

### Role-Based Access Flow

- **Admin:** Can upload documents, assign roles, and access all chat functionality
- **Doctor/Nurse:** Access to clinical documents and specialized medical information
- **Patient:** Limited access to general medical information
- **Other/Guest:** Basic access to public health content

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account
- Pinecone account
- Google AI API key
- Groq API key
- Git

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/rbac-medicalAssistant.git
cd rbac-medicalAssistant
```

### 2. Backend Setup (Server)

```bash
# Navigate to server directory
cd server

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup (Client)

```bash
# Navigate to client directory (from root)
cd client

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

Create a `.env` file in the root directory of the project:

```env
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=rbac_medical_db

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=medical-docs

# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here

# Optional: API URL for client (defaults to http://127.0.0.1:8000)
API_URL=http://127.0.0.1:8000
```

## ▶️ Running the Application

### Start the Backend Server

```bash
# From the server directory
cd server
# Activate virtual environment if not already
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the FastAPI server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The server will be available at `http://127.0.0.1:8000`

### Start the Frontend Client

```bash
# From the client directory (open new terminal)
cd client
# Activate virtual environment if not already
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the Streamlit app
streamlit run main.py
```

The client will be available at `http://localhost:8501`

## 📖 Usage

### 1. User Registration and Login

- Open the Streamlit client
- Use the Signup tab to create a new account
- Select your role (admin, doctor, nurse, patient, other)
- Login with your credentials

### 2. Admin Document Upload

Admins can upload PDF documents targeted to specific roles:

![Admin Upload](./assets/admin_upload.png)

- Select the target role for the document
- Upload a PDF file
- The document will be processed and stored in the vector database

### 3. Chat Interface

![Doctor Chat](./assets/doctor_chat.png)

- Enter your medical query in the chat input
- The system will retrieve relevant information based on your role
- Responses include sources from uploaded documents

### 4. Role-Based Access

- **Admin:** Full access to upload and chat
- **Doctor/Nurse:** Access to clinical documents
- **Patient:** General medical information
- **Other:** Basic health information

## 📡 API Documentation

The FastAPI backend provides the following endpoints:

| Method | Endpoint       | Description                      | Auth Required |
| ------ | -------------- | -------------------------------- | ------------- |
| GET    | `/health`      | Health check endpoint            | No            |
| POST   | `/signup`      | Register new user                | No            |
| GET    | `/login`       | Authenticate user                | HTTP Basic    |
| POST   | `/upload_docs` | Upload PDF document (Admin only) | HTTP Basic    |
| POST   | `/chat`        | Send chat message                | HTTP Basic    |

### API Examples

#### Health Check

```bash
curl http://127.0.0.1:8000/health
```

#### Signup

```bash
curl -X POST "http://127.0.0.1:8000/signup" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass", "role": "patient"}'
```

#### Login

```bash
curl -u "testuser:testpass" http://127.0.0.1:8000/login
```

#### Chat

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -u "testuser:testpass" \
     -d "message=What are the symptoms of diabetes?"
```

## 📁 Project Structure

```
rbac-medicalAssistant/
├── assets/                          # Images and documents
│   ├── thumbnail.png
│   ├── applicationFlow.png
│   ├── coreModules.png
│   ├── admin_upload.png
│   ├── doctor_chat.png
│   └── projectReport.pdf
├── server/                          # Backend FastAPI application
│   ├── main.py                      # FastAPI app entry point
│   ├── requirements.txt
│   ├── auth/                        # Authentication module
│   │   ├── routes.py
│   │   ├── models.py
│   │   └── hash_utils.py
│   ├── chat/                        # Chat and RAG module
│   │   ├── routes.py
│   │   └── chat_query.py
│   ├── docs/                        # Document processing module
│   │   ├── routes.py
│   │   └── vectorstore.py
│   ├── config/                      # Database configuration
│   │   └── db.py
│   └── uploaded_docs/               # Uploaded PDF storage
├── client/                          # Frontend Streamlit application
│   ├── main.py                      # Streamlit app entry point
│   └── requirements.txt
├── .env                             # Environment variables (create this)
├── .gitignore
└── README.md                        # This file
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines for Python code
- Add docstrings to functions and classes
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made by Meet Jain
