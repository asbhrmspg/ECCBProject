from dotenv import load_dotenv
import streamlit as st
import warnings
import os


load_dotenv()

# Ignore warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module='ipywidgets')
warnings.filterwarnings("ignore", category=RuntimeWarning, module='duckduckgo_search')
warnings.filterwarnings("ignore", category=ResourceWarning, module='zmq')

# Install packages only if needed (you can run these in requirements.txt instead)
# !pip install agno
# !pip install ddgs

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools

# 🛡️ Setup API key (either from environment or hardcoded here)
API_KEY = os.getenv("OPENROUTER_API_KEY")

# 🔧 Custom tools (replace these with actual tool imports or functions)
# You must define these tools somewhere or import them
commonscams2 = ...
financialliteracyquiz = ...
sidehustlegenerator = ...
currencyconverter = ...
budgetingfunction = ...
user_entereddata = ...

# 🚀 Initialize the agent
@st.cache_resource
def get_agent():
    return Agent(
        model=OpenRouter(
            id="google/gemini-2.5-flash",
            api_key=API_KEY,
            max_tokens=8000,
            temperature=0.7,
            top_p=0.9,
        ),
        tools=[
            DuckDuckGoTools(),
            commonscams2,
            financialliteracyquiz,
            sidehustlegenerator,
            currencyconverter,
            budgetingfunction,
            user_entereddata
        ],
        show_tool_calls=True,
        instructions = ("""
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

"""),
        add_history_to_messages=True
    )

agent = get_agent()

# 🧠 Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💼 Financial AI Agent")

# 🗨️ Show chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 📥 Chat input
user_input = st.chat_input("Ask a question about finance or business...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get agent response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        action_placeholder = st.empty() # For displaying tool actions
        satellite_placeholder = st.empty() # For displaying satellite images
        full_response = ""
        current_action = None

        # response = agent.run(user_input, stream=True)  # use print_response for CLI, get_response for raw text
        # st.markdown(response)

        try:

          # Get streaming response from agent
          response = agent.run(user_input, stream=True)  # use print_response for CLI, get_response for raw text


          # Display streaming response
          for chunk in response:
              # Handle different chunk types
              if hasattr(chunk, 'event'):
                  if chunk.event == 'RunResponseContent':
                      # Regular text content
                      if hasattr(chunk, 'content') and chunk.content:
                          full_response += chunk.content
                          # Clear any action display when we get content
                          if current_action:
                              action_placeholder.empty()
                              current_action = None

                # Searches for tools like duckduckgo for web searching
                  elif chunk.event == 'ToolCallStarted':
                      # Tool call started - show action
                      tool_name = chunk.tool.tool_name if hasattr(chunk.tool, 'tool_name') else "Unknown Tool"
                      current_action = f"🔧 Calling {tool_name}..."
                      action_placeholder.info(current_action)

                  elif chunk.event == 'ToolCallCompleted':
                      # Tool call completed
                      if current_action:
                          action_placeholder.success(f"✅ Tool call completed")
                          # Clear after a brief moment or keep until next content

              # Handle other chunk formats (fallback for different implementations)
              elif hasattr(chunk, 'content') and chunk.content:
                  full_response += chunk.content
                  if current_action:
                      action_placeholder.empty()
                      current_action = None
              elif isinstance(chunk, str):
                  full_response += chunk
                  if current_action:
                      action_placeholder.empty()
                      current_action = None

              # Update the message display with current response
              if full_response:
                  message_placeholder.markdown(full_response + "▌")


        except Exception as e:
            full_response = f"Error: {str(e)}"
            if current_action:
                action_placeholder.empty()

    # Final cleanup - clear action and show final message
    action_placeholder.empty()
    message_placeholder.markdown(full_response)

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": response})
