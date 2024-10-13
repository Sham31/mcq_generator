import streamlit as st
import PyPDF2
from io import BytesIO
from cryptography.fernet import Fernet

# Sample user credentials (in a real-world app, replace with a secure authentication system)
USER_CREDENTIALS = {
    "admin": "password123",  # username: password
}


# Encryption function (for file security)
def encrypt_file(data, key):
    """Encrypt the file content using a secret key."""
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(data.read())
    return encrypted_data


def decrypt_file(encrypted_data, key):
    """Decrypt the file content using the secret key."""
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data


# Generate a key for encryption
def generate_key():
    return Fernet.generate_key()


# Function to check if the document is machine-readable
def is_machine_readable(document):
    """Check if the document is machine-readable."""
    try:
        reader = PyPDF2.PdfReader(document)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""  # Handle None gracefully
        return bool(text.strip())  # If text exists, it's machine-readable
    except:
        return False  # If the document is not readable


# Function to convert document to a machine-readable format (dummy implementation for now)
def convert_to_machine_readable(document):
    """Convert document to a machine-readable format."""
    return "Conversion to machine-readable completed (dummy implementation)."


# Function to extract data from the document
def extract_data(document):
    """Extract key data from the document (dummy implementation)."""
    return {
        "Title": "Sample Document Title",
        "Author": "John Doe",
        "Date": "2023-09-28",
        "Summary": "This is a summary of the document's content."
    }


# Function to display the full text content of the document
def extract_full_text(document):
    """Extract the full text content from the PDF."""
    reader = PyPDF2.PdfReader(document)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() or ""  # Ensure to handle None gracefully
    return full_text


# Authentication Function
def login(username, password):
    """Check if the username and password are correct."""
    return USER_CREDENTIALS.get(username) == password


# Initialize session state for login status
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Display login page if not logged in
if not st.session_state['logged_in']:
    st.title("🔐 User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.session_state['logged_in'] = True
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect username or password.")
else:
    # User is logged in - show the main application
    st.title("TransformoDocs: Document Transformation Application")
    st.write("""
    This application helps organizations transform non-machine-readable documents into machine-readable formats.
    It also provides workflows for data extraction, compliance checking, and ensures the quality of the processed data.
    """)

    # Sidebar document upload
    uploaded_file = st.file_uploader("Upload a PDF or encrypted file", type=['pdf', 'enc'])

    if uploaded_file is not None:
        # Display file details in the sidebar
        file_details = {
            "Filename": uploaded_file.name,
            "Filetype": uploaded_file.type,
            "Filesize (KB)": round(uploaded_file.size / 1024, 2)
        }
        st.header("📂 Uploaded File Details")
        st.write(file_details)

        # Sidebar options for actions
        st.subheader("Actions")
        check_readability = st.checkbox("🔍 Check Machine-Readability")
        convert_option = st.checkbox("🔄 Convert to Machine-Readable")
        extract_data_option = st.checkbox("📄 Extract Data")
        encrypt_option = st.checkbox("🔐 Encrypt Document")
        decrypt_option = st.checkbox("🔓 Decrypt Document")

        # Step 2: Check if the document is machine-readable
        if check_readability:
            st.header("Step 2: Document Ingestion and Readability Check")
            if is_machine_readable(uploaded_file):
                st.success("The document is machine-readable and can be processed.")
            else:
                st.warning("The document is NOT machine-readable.")

        # Step 3: Convert document to machine-readable format (if chosen)
        if convert_option:
            st.header("Step 3: Convert Document to Machine-Readable Format")
            if st.button("Convert Document"):
                result = convert_to_machine_readable(uploaded_file)
                st.success(result)

        # Step 4: Data Extraction and Show Content
        if extract_data_option:
            st.header("Step 4: Extract Data and Show File Content")
            if st.button("Extract Data from Document"):
                extracted_data = extract_data(uploaded_file)
                st.write("📋 Extracted Data:", extracted_data)

                # Show the full text content of the file
                st.subheader("📝 Document Content:")
                full_text = extract_full_text(uploaded_file)
                st.text_area("Full Text", full_text, height=300)

        # Step 6: Encrypt the document (optional)
        if encrypt_option:
            st.header("Step 6: Encrypt Document")
            if st.button("Encrypt Document"):
                # Generate the encryption key
                encryption_key = generate_key()
                encrypted_data = encrypt_file(uploaded_file, encryption_key)
                st.success("Document has been encrypted successfully!")

                # Display and allow download of encryption key and encrypted file
                st.write(f"**Decryption Key**: `{encryption_key.decode()}` (Store this securely!)")
                st.download_button("Download Encrypted Document", encrypted_data, file_name="encrypted_document.enc")

        # Step 7: Decrypt the document (optional)
        if decrypt_option:
            st.header("Step 7: Decrypt Document")
            decryption_key = st.text_input("Enter the decryption key")
            if st.button("Decrypt Document"):
                try:
                    # Read encrypted data as raw bytes
                    encrypted_data = uploaded_file.read()
                    decrypted_data = decrypt_file(encrypted_data, decryption_key.encode())
                    st.success("Document has been decrypted successfully!")

                    # Display the decrypted data or provide download
                    decrypted_pdf = BytesIO(decrypted_data)
                    st.download_button("Download Decrypted Document", decrypted_pdf, file_name="decrypted_document.pdf")
                except Exception as e:
                    st.error(f"Decryption failed. Please check the key and try again. Error: {e}")

    else:
        st.write("Please upload a PDF or encrypted file to start the process.")

    # Right sidebar for additional features
    with st.sidebar:
        st.header("📝 Helpful Information")
        st.write("""
        - Ensure your document is clear and not scanned to maximize machine readability.
        - Use simple filenames without special characters.
        - For best results, upload documents that have been created digitally.
        """)

        # Recent files section
        st.header("📊 Recent Files")
        st.write("""
        - File1.pdf
        - File2.doc
        - File3.docx
        """)

        # Feedback section
        st.header("📧 Feedback")
        feedback = st.text_area("Your feedback:", placeholder="Let us know your thoughts...")
        if st.button("Submit Feedback"):
            st.success("Thank you for your feedback!")

        # Security section
        st.header("🔒 Security Notices")
        st.write("""
        - Always encrypt sensitive documents before uploading.
        - Avoid sharing login credentials.
        - Regularly update your password for security.
        """)

        # Upcoming features section
        st.header("📈 Upcoming Features")
        st.write("""
        - Integration with cloud storage for document management.
        - AI-driven analytics to extract deeper insights.
        - Support for more document formats in the future.
        """)

        # Notifications
        st.header("🔔 Notifications")
        st.write("""
        - Stay tuned for updates!
        - Check your email for new features and tips.
        """)

    # Logout option
    if st.button("Logout"):
        # Set logged_in state to False to simulate logout
        st.session_state['logged_in'] = False

        # Clear all features or display the login page after logout
        st.write("You have been logged out. Please refresh the page to login again.")
        st.stop()  # Stop the execution to prevent further content from showing
