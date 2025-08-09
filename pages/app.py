from dotenv import load_dotenv
import streamlit as st
import tempfile
import PyPDF2
import os

# Import the modularized agent utilities
from pages.agent import detect_user_location, agent as run_agent
from pages.eccb_map import render_eccu_map

# ✅✅✅ added here
# from pages.agent import agent

load_dotenv()

# All agent internals moved to agent.py

# Function to extract text from PDF files
def extract_pdf_text(pdf_file):
    """
    Extract text content from a PDF file using PyPDF2

    Args:
        pdf_file: Uploaded file object from Streamlit

    Returns:
        str: Extracted text content from the PDF
    """
    try:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text_content = ""

        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content += page.extract_text() + "\n"

        return text_content.strip()
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# Function to read text from other file types
def read_text_file(file):
    """
    Read text content from various file types

    Args:
        file: Uploaded file object from Streamlit

    Returns:
        str: File content as text
    """
    try:
        # Try to decode as UTF-8 first
        content = file.read().decode('utf-8')
        return content
    except UnicodeDecodeError:
        try:
            # Try with different encoding if UTF-8 fails
            file.seek(0)  # Reset file pointer
            content = file.read().decode('latin-1')
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"


# 🧠 Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💼 Financial AI Agent")

# 🌐 Detect user location early and show a tiny badge
location = detect_user_location()
loc_country = location.get("country") or "Unknown"
loc_city = location.get("city") or ""
loc_is_eccu = location.get("is_eccu")
badge = f"📍 {loc_city + ', ' if loc_city else ''}{loc_country}"
st.caption(badge + ("  ·  ECCU" if loc_is_eccu else "  ·  Global"))
render_eccu_map()

# 🗨️ Show chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# No quick-start or auto-generated prompts — minimal first page

# ✅✅ changes here
# 📥 Chat input + added accept file here
# CHANGED USER INPUT VARIABLE TO DATA
if data := st.chat_input("Ask me anything...", accept_file=True):

    # Extract text prompt and uploaded files from the input data
    prompt = data.get("text", None)
    uploaded_files = data.get("files", None)

    # Initialize user message
    user_message = {"role": "user", "content": prompt}

    # Process uploaded files if any
    file_content = ""
    image_files = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name.lower()
            file_extension = file_name.split('.')[-1] if '.' in file_name else ""

            # Handle different file types
            if file_extension == "pdf":
                # Extract text from PDF files
                pdf_text = extract_pdf_text(uploaded_file)
                file_content += f"\n\n**PDF Content ({file_name}):**\n{pdf_text}\n"

            elif file_extension in ["txt", "md", "py", "js", "html", "css", "json", "xml", "csv"]:
                # Read text-based files
                text_content = read_text_file(uploaded_file)
                file_content += f"\n\n**File Content ({file_name}):**\n{text_content}\n"

            elif file_extension in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                # Handle image files
                image_files.append(uploaded_file)
                user_message["image"] = uploaded_file

            else:
                # For unsupported file types, try to read as text
                try:
                    text_content = read_text_file(uploaded_file)
                    file_content += f"\n\n**File Content ({file_name}):**\n{text_content}\n"
                except:
                    file_content += f"\n\n**Unsupported file type: {file_name}**\n"

    # Combine prompt with file content
    if file_content:
        user_message["content"] = (prompt or "") + file_content

    # Add user message to chat history
    st.session_state.messages.append(user_message)

    # Display user message in chat
    with st.chat_message("user"):
        if image_files:
            for img_file in image_files:
                st.image(img_file, width=200)
        st.markdown(user_message["content"])

    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        action_placeholder = st.empty()  # For displaying tool actions
        full_response = ""
        current_action = None

        try:
            # Handle image files for the agent
            image_path = None
            if image_files:
                # Create temporary file for the first image (agent can handle one image at a time)
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_files[0].name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(image_files[0].getvalue())
                    image_path = tmp_file.name

            # Get streaming response from the AI agent
            response_stream = run_agent(st.session_state.messages, image_path, location=location)

            # Process and display the streaming response
            for chunk in response_stream:
                # Handle different types of response chunks
                if hasattr(chunk, 'event'):
                    if chunk.event == 'RunResponseContent':
                        # Regular text content from the AI
                        if hasattr(chunk, 'content') and chunk.content:
                            full_response += chunk.content
                            # Clear any action display when we get content
                            if current_action:
                                action_placeholder.empty()
                                current_action = None

                    elif chunk.event == 'ToolCallStarted':
                        # Tool call started - show action indicator
                        tool_name = chunk.tool.tool_name if hasattr(chunk.tool, 'tool_name') else "Unknown Tool"
                        current_action = f"🔧 Calling {tool_name}..."
                        action_placeholder.info(current_action)

                    elif chunk.event == 'ToolCallCompleted':
                        # Tool call completed
                        if current_action:
                            action_placeholder.success(f"✅ Tool call completed")
                            # Clear after a brief moment or keep until next content

                # Update the message display with current response
                if full_response:
                    message_placeholder.markdown(full_response + "● ")

            # Clean up temporary image file
            if image_path:
                os.unlink(image_path)

        except Exception as e:
            # Handle any errors during response generation
            full_response = f"Error: {str(e)}"
            if current_action:
                action_placeholder.empty()

        # Final cleanup - clear action indicator and show final message
        action_placeholder.empty()
        message_placeholder.markdown(full_response)

    # Add assistant response to chat history
    assistant_message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(assistant_message)
