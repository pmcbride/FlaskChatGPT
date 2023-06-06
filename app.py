#%% Import Flask and create an app object
import config
from dotenv import load_dotenv
load_dotenv()

import os
import json
import asyncio
import openai
import pprint as pp
import markdown

# openai.api_key = os.getenv("OPENAI_API_KEY")
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# Import Flask and create an app object
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

# Import asyncio and the async_playwright module from Playwright
import asyncio
from playwright.async_api import async_playwright

# Import LangChain and other modules
import langchain
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, load_tools


from langchain.agents.agent_toolkits import PlayWrightBrowserToolkit
from langchain.tools.playwright.utils import (
    create_async_playwright_browser,
    create_sync_playwright_browser, # A synchronous browser is available, though it isn't compatible with jupyter.
)

# This import is required only for jupyter notebooks, since they have their own eventloop
# import nest_asyncio
# nest_asyncio.apply()

#%% Agent
def get_agent():
    # LLM using ChatOpenAI
    llm = ChatOpenAI(model_name="gpt-4", temperature=0)  # Also works well with Anthropic models
    # Get the tools from the toolkit
    tools = load_tools(["serpapi"], llm=llm)
    # Create an agent using ChatOpenAI and initialize it with tools and handle_parsing_errors=True
    agent_chain = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True
    )

# agent_chain = get_agent()

#%%

@app.route("/")
def home():
    # Use some initial chat history (empty, in this case)
    chat_history = []
    return render_template("chat.html", chat_history=chat_history)


@app.route("/respond")
def respond():
    """ Create another route for your chatbot logic
    """
    print("\nrespond::start:")
    # Get the user message and the chat history from the interface
    message = request.args.get("message")
    print(f"  respond::message: {message}")
    # Parse the chat history as a JSON object
    chat_history = json.loads(request.args.get("chat_history", "[]"))
    print(f"  respond::chat_history: {chat_history}")
    # Run your main coroutine that handles the chatbot logic
    # response = asyncio.run(main(message, chat_history))
    chat_history = main(message, chat_history)
    response = jsonify({"chat_history": chat_history})
    print("\nrespond::return:")
    print(f"  respond::chat_history: {chat_history}")
    # print response to console as json
    pp.pprint(response.json)

    # Return the response as a JSON string
    return response


def main(message, chat_history):
    """ Define your main coroutine that handles the chatbot logic
    """
    print("\nmain::start:")
    print(f"  main::message: {message}")
    print(f"  main::chat_history: {chat_history}")
    # Run your agent chain with the user message as input and get the bot message as output
    bot_message = "I'm a STICK!!!\n\n```python\nprint('Hello World')\n```"
    # Convert bot_message to HTML
    bot_message_html = markdown.markdown(bot_message)

    # Append the user message and the bot message to the chat history
    chat_history[-1][1] = bot_message_html

    print("\nmain::return:")
    print(f"  main::bot_message: {bot_message}")
    print(f"  main::bot_message_html: {bot_message_html}")
    print(f"  main::chat_history: {chat_history}")
    
    # Return the updated chat history as a string
    return chat_history

# def main(message, chat_history):
#     """ Define your main coroutine that handles the chatbot logic
#     """
#     print("\nmain::start:")
#     print(f"  main::message: {message}")
#     print(f"  main::chat_history: {chat_history}")
#     # Run your agent chain with the user message as input and get the bot message as output
#     # bot_message = "I'm a STICK!!!\n\n```python\nprint('Hello World')\n```" # agent_chain.run(input=message)
#     bot_message = "I'm a STICK!!!<br><br><pre><code>print('Hello World')</code></pre>"
#     print("\nmain::return:")
#     print(f"  main::bot_message: {bot_message}")

#     # Append the user message and the bot message to the chat history
#     chat_history[-1][1] = bot_message
#     print(f"  main::chat_history: {chat_history}")
    
#     # Return the updated chat history as a string
#     return chat_history

async def amain(message, chat_history):
    """ Define your main coroutine that handles the chatbot logic
    """
    # Create one event loop before creating the tools
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Use async with to create and close the async browser automatically
    async with async_playwright() as playwright:
        # Use await to launch a Chromium browser asynchronously
        browser = await playwright.chromium.launch()
        # Create a PlayWrightBrowserToolkit from the browser
        browser_toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        # Get the tools from the toolkit
        tools = browser_toolkit.get_tools()

        # Create an agent using ChatOpenAI and initialize it with tools and handle_parsing_errors=True
        llm = ChatOpenAI(model_name="gpt-4", temperature=0)  # Also works well with Anthropic models
        agent_chain = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )

        # Run your agent chain with the user message as input and get the bot message as output
        bot_message = await agent_chain.arun(input=message)

        # Append the user message and the bot message to the chat history
        chat_history.append((message, bot_message))

        # Return the updated chat history as a string
        return str(chat_history)

# Run your Flask app with app.run()
if __name__ == "__main__":
    app.run(
        host="localhost",
        port=None,
        debug=True,
        load_dotenv=True,
    )
