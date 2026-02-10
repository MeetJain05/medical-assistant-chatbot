import streamlit as st
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
import os
from requests.exceptions import ConnectionError, Timeout, RequestException


load_dotenv()


API_URL = os.getenv("API_URL") or "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10  # seconds

if not os.getenv("API_URL"):
    st.warning("⚠️ API_URL not set; defaulting to http://127.0.0.1:8000")

st.set_page_config(page_title="Healthcare RBAC RAG Chatbot",layout="centered")

# Session state initalization
if "username" not in st.session_state:
    st.session_state.username=""
    st.session_state.password=""
    st.session_state.role=""
    st.session_state.logged_in=False
    st.session_state.mode="auth"

# Error handling helper
def handle_api_error(response, operation_name):
    """Handle API errors gracefully with user-friendly messages"""
    try:
        error_data = response.json()
        detail = error_data.get("detail", f"{operation_name} failed")
    except (ValueError, AttributeError):
        detail = f"{operation_name} failed (HTTP {response.status_code}): {response.text[:200]}"
    
    return detail

def handle_connection_error(e, operation_name):
    """Handle connection and timeout errors"""
    if isinstance(e, Timeout):
        return f"⏱️ {operation_name} timed out. The server took too long to respond. Please try again."
    elif isinstance(e, ConnectionError):
        return f"🔌 Cannot connect to the server. Please verify:\n- The server is running\n- API_URL is correct: {API_URL}\n- Internet connection is active"
    else:
        return f"❌ {operation_name} failed: {str(e)[:150]}"

# Auth header
def get_auth():
    return HTTPBasicAuth(st.session_state.username,st.session_state.password)

# Auth UI

def auth_ui():
    st.title("Healthcare RBAC RAG")
    st.subheader("Login or Signup")

    tab1,tab2=st.tabs(["Login","Signup"])

    # Login
    with tab1:
        username=st.text_input("Username",key="login_user")
        password=st.text_input("Password",type="password",key="login_pass")
        if st.button("Login"):
            # Input validation
            if not username.strip():
                st.error("❗ Username cannot be empty")
            elif not password:
                st.error("❗ Password cannot be empty")
            else:
                try:
                    with st.spinner("Authenticating..."):
                        res=requests.get(
                            f"{API_URL}/login",
                            auth=HTTPBasicAuth(username, password),
                            timeout=REQUEST_TIMEOUT
                        )
                    
                    if res.status_code==200:
                        user_data=res.json()
                        st.session_state.username=username
                        st.session_state.password=password
                        st.session_state.role=user_data["role"]
                        st.session_state.logged_in=True
                        st.session_state.mode="chat"
                        st.success(f"✅ Welcome {username}")
                        st.rerun()
                    elif res.status_code == 401:
                        st.error("❌ Invalid username or password")
                    elif res.status_code == 404:
                        st.error("❌ User not found. Please sign up first.")
                    else:
                        detail = handle_api_error(res, "Login")
                        st.error(f"❌ {detail}")
                
                except (ConnectionError, Timeout, RequestException) as e:
                    error_msg = handle_connection_error(e, "Login")
                    st.error(error_msg)
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)[:150]}")


    # Signup
    with tab2:
        new_user=st.text_input("New Username",key="signup_user")
        new_pass=st.text_input("New Password",type="password",key="signup_pass")
        new_role=st.selectbox("Choose Role",["admin","doctor","nurse","patient","other"])
        if st.button("Signup"):
            # Input validation
            if not new_user.strip():
                st.error("❗ Username cannot be empty")
            elif not new_pass:
                st.error("❗ Password cannot be empty")
            elif len(new_pass) < 4:
                st.error("❗ Password must be at least 4 characters")
            else:
                try:
                    with st.spinner("Creating account..."):
                        payload={"username":new_user,"password":new_pass,"role":new_role}
                        res=requests.post(
                            f"{API_URL}/signup",
                            json=payload,
                            timeout=REQUEST_TIMEOUT
                        )
                    
                    if res.status_code==200:
                        st.success("✅ Signup successful! You can now login.")
                    elif res.status_code == 400:
                        st.error("❌ User already exists. Please try a different username.")
                    else:
                        detail = handle_api_error(res, "Signup")
                        st.error(f"❌ {detail}")
                
                except (ConnectionError, Timeout, RequestException) as e:
                    error_msg = handle_connection_error(e, "Signup")
                    st.error(error_msg)
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)[:150]}")



# Upload PDF (Admin only)
def upload_docs():
    st.subheader("Upload PDF for specific Role")
    uploaded_file=st.file_uploader("Choose a PDF file",type=["pdf"])
    role_for_doc=st.selectbox("Target Role for docs",["doctor","nurse","patient","other"])

    if st.button("Upload Document"):
        if not uploaded_file:
            st.warning("⚠️ Please select a PDF file")
        else:
            try:
                with st.spinner("Uploading document..."):
                    files={"file":(uploaded_file.name,uploaded_file.getvalue(),"application/pdf")}
                    data={"role":role_for_doc}
                    res=requests.post(
                        f"{API_URL}/upload_docs",
                        files=files,
                        data=data,
                        auth=get_auth(),
                        timeout=REQUEST_TIMEOUT
                    )
                
                if res.status_code==200:
                    doc_info=res.json()
                    st.success(f"✅ Uploaded: {uploaded_file.name}")
                    st.info(f"📄 Doc ID: {doc_info['doc_id']}\n📊 Access: {doc_info['accessible_to']}")
                elif res.status_code == 401:
                    st.error("❌ Unauthorized. Please login again.")
                elif res.status_code == 403:
                    st.error("❌ You don't have permission to upload documents.")
                else:
                    detail = handle_api_error(res, "Upload")
                    st.error(f"❌ {detail}")
            
            except (ConnectionError, Timeout, RequestException) as e:
                error_msg = handle_connection_error(e, "Upload")
                st.error(error_msg)
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)[:150]}")



# chat interface
def chat_interface():
    st.subheader("Ask a healthcare question")
    msg=st.text_input("Your query")

    if st.button("Send"):
        if not msg.strip():
            st.warning("⚠️ Please enter a query")
        else:
            try:
                with st.spinner("Processing your question..."):
                    res=requests.post(
                        f"{API_URL}/chat",
                        data={"message":msg},
                        auth=get_auth(),
                        timeout=REQUEST_TIMEOUT
                    )
                
                if res.status_code==200:
                    reply=res.json()
                    st.markdown('### 💡 Answer')
                    st.success(reply["answer"])
                    if reply.get("sources"):
                        st.markdown("**📚 Sources:**")
                        for src in reply["sources"]:
                            st.write(f"- {src}")
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


# main flow
if not st.session_state.logged_in:
    auth_ui()
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"Welcome, {st.session_state.username}")
        st.markdown(f"**Role**: `{st.session_state.role}`")
    with col2:
        if st.button("🚪 Logout"):
            try:
                st.session_state.logged_in=False
                st.session_state.username=""
                st.session_state.password=""
                st.session_state.role=""
                st.session_state.mode="auth"
                st.success("✅ Logged out successfully")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error during logout: {str(e)[:150]}")
                st.info("Refreshing page...")
                st.rerun()


    if st.session_state.role=="admin":
        upload_docs()
        st.divider()
        chat_interface()
    else:
        chat_interface()
