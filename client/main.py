import streamlit as st
from dotenv import load_dotenv
import requests
import os
from requests.exceptions import ConnectionError, Timeout, RequestException


load_dotenv()

# Page config
st.set_page_config(
    page_title="🏥 Healthcare RBAC Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    :root {
        --primary: #0066CC;
        --success: #28A745;
        --danger: #DC3545;
        --warning: #FFC107;
    }
    
    .main {
        padding-top: 2rem;
    }
    
    .auth-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .dashboard-header {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: bold;
    }
    
    .chat-response {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

API_URL = os.getenv("API_URL") or "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10

if not os.getenv("API_URL"):
    st.warning("⚠️ API_URL not configured. Using localhost.")


# Session state initialization
if "access_token" not in st.session_state:
    st.session_state.access_token = None
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.logged_in = False


# Helper functions
def make_auth_header():
    """Create authorization header with JWT token"""
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}


def handle_api_error(response, operation_name):
    """Handle API errors gracefully"""
    try:
        error_data = response.json()
        detail = error_data.get("detail", f"{operation_name} failed")
    except (ValueError, AttributeError):
        detail = f"{operation_name} failed (HTTP {response.status_code}): {response.text[:200]}"
    return detail


def handle_connection_error(e, operation_name):
    """Handle connection and timeout errors"""
    if isinstance(e, Timeout):
        return f"⏱️ {operation_name} timed out. Please try again."
    elif isinstance(e, ConnectionError):
        return f"🔌 Cannot connect to server. Check if API is running at: {API_URL}"
    else:
        return f"❌ {operation_name} failed: {str(e)[:150]}"

# Auth UI
def auth_ui():
    """Authentication interface with improved UI"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## 🏥 Healthcare RBAC Assistant")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Signup"])
        
        # Login Tab
        with tab1:
            st.markdown("### Welcome Back")
            username = st.text_input("👤 Username", key="login_user")
            password = st.text_input("🔒 Password", type="password", key="login_pass")
            
            if st.button("Login", use_container_width=True):
                if not username.strip():
                    st.error("❗ Username cannot be empty")
                elif not password:
                    st.error("❗ Password cannot be empty")
                else:
                    try:
                        with st.spinner("🔍 Authenticating..."):
                            res = requests.post(
                                f"{API_URL}/login",
                                params={"username": username, "password": password},
                                timeout=REQUEST_TIMEOUT
                            )
                        
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.access_token = data["access_token"]
                            st.session_state.username = data["username"]
                            st.session_state.role = data["role"]
                            st.session_state.logged_in = True
                            st.success(f"✅ Welcome {username}!")
                            st.rerun()
                        elif res.status_code == 401:
                            st.error("❌ Invalid username or password")
                        else:
                            detail = handle_api_error(res, "Login")
                            st.error(f"❌ {detail}")
                    
                    except (ConnectionError, Timeout, RequestException) as e:
                        error_msg = handle_connection_error(e, "Login")
                        st.error(error_msg)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)[:150]}")
        
        # Signup Tab
        with tab2:
            st.markdown("### Create Account")
            new_user = st.text_input("👤 Username", key="signup_user")
            new_pass = st.text_input("🔒 Password", type="password", key="signup_pass")
            new_role = st.selectbox(
                "👨‍⚕️ Role",
                ["admin", "doctor", "nurse", "patient", "other"],
                index=3
            )
            
            if st.button("Create Account", use_container_width=True):
                if not new_user.strip():
                    st.error("❗ Username cannot be empty")
                elif not new_pass:
                    st.error("❗ Password cannot be empty")
                elif len(new_pass) < 4:
                    st.error("❗ Password must be at least 4 characters")
                else:
                    try:
                        with st.spinner("📝 Creating account..."):
                            payload = {"username": new_user, "password": new_pass, "role": new_role}
                            res = requests.post(
                                f"{API_URL}/signup",
                                json=payload,
                                timeout=REQUEST_TIMEOUT
                            )
                        
                        if res.status_code == 200:
                            st.success("✅ Account created! You can now login.")
                        elif res.status_code == 400:
                            st.error("❌ Username already exists.")
                        else:
                            detail = handle_api_error(res, "Signup")
                            st.error(f"❌ {detail}")
                    
                    except (ConnectionError, Timeout, RequestException) as e:
                        error_msg = handle_connection_error(e, "Signup")
                        st.error(error_msg)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)[:150]}")


# Upload Documents (Admin only)
def upload_docs():
    with st.expander("📤 Upload Documents", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        
        with col2:
            role_for_doc = st.selectbox(
                "Target Role for docs",
                ["doctor", "nurse", "patient", "other"],
                key="doc_role"
            )
        
        if st.button("📤 Upload Document", use_container_width=True):
            if not uploaded_file:
                st.warning("⚠️ Please select a PDF file")
            else:
                try:
                    with st.spinner("📤 Uploading document..."):
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        data = {"role": role_for_doc}
                        res = requests.post(
                            f"{API_URL}/upload_docs",
                            files=files,
                            data=data,
                            headers=make_auth_header(),
                            timeout=REQUEST_TIMEOUT
                        )
                    
                    if res.status_code == 200:
                        doc_info = res.json()
                        st.success(f"✅ Uploaded: {uploaded_file.name}")
                        st.info(f"📄 Doc ID: {doc_info['doc_id']}\n📊 Access: {doc_info['accessible_to']}")
                    elif res.status_code == 401:
                        st.error("❌ Session expired. Please login again.")
                    elif res.status_code == 403:
                        st.error("❌ Only admins can upload documents.")
                    else:
                        detail = handle_api_error(res, "Upload")
                        st.error(f"❌ {detail}")
                
                except (ConnectionError, Timeout, RequestException) as e:
                    error_msg = handle_connection_error(e, "Upload")
                    st.error(error_msg)
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)[:150]}")


# Chat Interface
def chat_interface():
    st.markdown("### 💬 Ask a Question")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        message = st.text_input("Your query", placeholder="Ask anything about the documents...")
    
    with col2:
        send_btn = st.button("📤 Send", use_container_width=True)
    
    if send_btn:
        if not message.strip():
            st.warning("⚠️ Please enter a query")
        else:
            try:
                with st.spinner("🔍 Processing your question..."):
                    res = requests.post(
                        f"{API_URL}/chat",
                        data={"message": message},
                        headers=make_auth_header(),
                        timeout=REQUEST_TIMEOUT
                    )
                
                if res.status_code == 200:
                    reply = res.json()
                    st.markdown('<div class="chat-response">', unsafe_allow_html=True)
                    st.markdown("### 💡 Answer")
                    st.markdown(reply["answer"])
                    
                    if reply.get("sources"):
                        st.markdown("**📚 Sources:**")
                        for src in reply["sources"]:
                            st.markdown(f"- {src}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                elif res.status_code == 401:
                    st.error("❌ Session expired. Please login again.")
                elif res.status_code == 403:
                    st.error("❌ You don't have access to this query.")
                else:
                    detail = handle_api_error(res, "Chat")
                    st.error(f"❌ {detail}")
            
            except (ConnectionError, Timeout, RequestException) as e:
                error_msg = handle_connection_error(e, "Chat")
                st.error(error_msg)
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)[:150]}")


# Main Flow
if not st.session_state.logged_in:
    auth_ui()
else:
    # Header with user info and logout
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>🏥 Healthcare RBAC Assistant</h1>
        <p style="font-size: 18px; margin-top: 1rem;">
            Welcome, <strong>{st.session_state.username}</strong> • Role: <strong>{st.session_state.role.upper()}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with logout
    with st.sidebar:
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**User:** {st.session_state.username}")
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.access_token = None
                st.session_state.username = ""
                st.session_state.role = ""
                st.session_state.logged_in = False
                st.success("✅ Logged out successfully")
                st.rerun()
    
    # Main content
    st.markdown("---")
    
    # Admin section
    if st.session_state.role == "admin":
        upload_docs()
        st.markdown("---")
    
    # Chat interface
    chat_interface()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: gray;'>"
        "🏥 Healthcare RBAC RAG System • Powered by LangChain & Pinecone"
        "</p>",
        unsafe_allow_html=True
    )
