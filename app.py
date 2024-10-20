import chainlit as cl
import dotenv
import os
import pandas as pd 
import whisper
from datetime import datetime
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from openai import OpenAI

from classes import SessionState

from utils_callbacks import callback_run_scenario, callback_start_scenario, callback_evaluate_performance, callback_display_queries_responses
from utils_customer_research import get_latest_news
from utils_pose_objections import pose_objections
from utils_prep import prep_research, prep_opportunities, prep_start, prep_opportunity_analysis
from utils_simulation import do_simulation



dotenv.load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

def set_session_state_variables(session_state):
    if "DO_CUSTOMER_RESEARCH" in os.environ:
        do_customer_research = os.getenv("DO_CUSTOMER_RESEARCH")
        if do_customer_research.lower() == "true":
            session_state.do_customer_research = True
        else:
            session_state.do_customer_research = False


llm_model = "gpt-4o-mini"
set_llm_cache(InMemoryCache())
client = OpenAI(api_key=openai_api_key)
whisper_model = whisper.load_model("base")

#############################################
# Action callbacks
#############################################

@cl.action_callback("Deal Analysis")
async def on_action_anayze_deal(action):
    session_state = cl.user_session.get("session_state", None)
    await prep_opportunities(session_state)

@cl.action_callback("Customer Research")
async def on_action_anayze_deal(action):
    session_state = cl.user_session.get("session_state", None)
    await get_latest_news("HSBC")

@cl.action_callback("Sales Simulation")
async def on_action_sales_simulation(action):
    session_state = cl.user_session.get("session_state", None)
    await callback_run_scenario(action)

@cl.action_callback("HSBC: Lending - Loan Origination System (Proposal)")
async def on_action_anayze_opportunity(action):
    await prep_opportunity_analysis()

@cl.action_callback("Get Latest News on this Customer")
async def on_action_get_latest_news(action):
    await get_latest_news(action.value)

@cl.action_callback("Enter Meeting Simulation")
async def on_action_run_scenario(action):
    await callback_run_scenario(action)

@cl.action_callback("Start Simulation")
async def on_action_start_scenario(action):
    print("on_action_start_scenario()")
    await callback_start_scenario()

@cl.action_callback("Evaluate Performance")
async def on_action_evaluate_performance(action):
    await callback_evaluate_performance()

@cl.action_callback("Display Queries and Responses")
async def on_action_display_queries_responses(action):
    await callback_display_queries_responses()



#############################################
### On Chat Start (Session Start) Section ###
#############################################
@cl.on_chat_start
async def on_chat_start():
    session_state = SessionState()
    set_session_state_variables(session_state)
    cl.user_session.set("session_state", session_state)
    session_state.llm_model = llm_model
    print(session_state)
    cl.user_session.set("messages", [])
    if client is None:
        await cl.Message(content="Error: OpenAI client not initialized. Please check your API key.").send()
    if whisper_model is None:
        await cl.Message(content="Error: Whisper model not loaded. Please check your installation.").send()

    await prep_start(session_state)

    # await prep_opportunities(session_state)

    # await prep_opportunity_analysis(session_state)

    # await prep_research(session_state)
    # session_state.session_stage = "research"

    # Ask for the first PDF file (Potential Customer Business Domain)
    # await process_pdf_files()
    

@cl.on_message
async def main(message):
    content = message.content.strip()
    session_state = cl.user_session.get("session_state", None)
    if session_state is None:
        await cl.Message(content="Error: Session state not initialized. Please check your installation.").send()
        return
    if session_state.do_objections:
        await pose_objections(session_state)
    else:
        await do_simulation(client, session_state, message)