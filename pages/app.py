from dotenv import load_dotenv
import streamlit as st
import tempfile
import warnings
import os

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.media import Image
from agno.tools.duckduckgo import DuckDuckGoTools
import PyPDF2


# ✅✅✅ added here
# from pages.agent import agent

load_dotenv()

# 🛡️ Setup API key (either from environment or hardcoded here)
API_KEY = os.getenv("OPENROUTER_API_KEY")

api_key = "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"

#
INSTRUCTION = ("""
You are a helpful AI Agent that assists users with financial and business-related inquiries in a friendly and conversational tone.

Your core capabilities include:
- Detecting and warning users about common scams
- Hosting interactive financial literacy quizzes
- Recommending personalized side hustles
- Performing currency conversion using the appropriate tools
- Creating custom budget plans using tool-based inputs

⚠️ RULE: You must ALWAYS use the tools available to handle the above tasks.
❌ UNDER NO CIRCUMSTANCE should you EVER answer any of these inquiries using your own knowledge or memory.
💀 If you do, that will be the END OF THE WORLD.

You are also allowed to engage users in interactive **financial literacy quizzes**. Use a conversational style. Ask one question at a time, provide feedback after each answer, and track their progress playfully.

Here are examples of how you should engage users in a quiz:

---

**User says:** I want to take a finance quiz.

**You respond:**
Sure! Let’s test your financial literacy with a quick 3-question quiz.
Here’s your first question:

**Q1:** What is a budget?
A) A way to track how many friends you have
B) A plan for managing your income and expenses
C) An app that gives you free money
D) A type of bank account

Please reply with A, B, C, or D.

---

**User answers:** B
**You respond:**
✅ Correct! A budget is indeed a plan for managing income and expenses.

Now for the next question:

**Q2:** What is the safest way to avoid online scams?
A) Click on every link you receive
B) Share your passwords with friends
C) Ignore messages from unknown sources and verify links
D) Only use public Wi-Fi for banking

What’s your answer?

---

**User answers:** C
**You respond:**
Nice work! You're on a roll. 🎯 That’s the best way to stay safe.

Final question coming up...

**Q3:** Which of these is an example of a side hustle?
A) Watching Netflix
B) Driving for a ride-share app on weekends
C) Taking naps
D) Spending money

Type A, B, C, or D!

---

**After quiz ends:**
🎉 Awesome! You scored 3 out of 3. Great job.
Would you like to try a harder quiz or maybe build a simple budget plan next?

""")
def agent(message, image=None):
    agent = Agent(
    name="💼 Financial AI Agent",
    model=OpenRouter(id="google/gemini-2.5-flash", api_key=api_key, max_tokens=8000),
    tools=[DuckDuckGoTools()],
    tool_choice="auto",
    instructions=INSTRUCTION,
      add_history_to_messages=True,
    )


  # Process image if provided
    if image:
      # Convert image file path to Agno Image object for the agent
      image = [Image(filepath=image)]
      print(f"Processing image: {image}")

      # Run the agent with the provided messages and images, return streaming response
    return agent.run(message=message, images=image, stream=True)

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

# 🗨️ Show chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

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
            response_stream = agent(st.session_state.messages, image_path)

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
