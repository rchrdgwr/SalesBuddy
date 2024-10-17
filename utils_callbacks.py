
import asyncio
import chainlit as cl
from datetime import datetime
from utils_data import  get_company_data, get_opportunities, get_questions, get_customer_background
from utils_output import display_evaluation_results, display_llm_responses
from utils_objections import create_objections
# async def callback_show_scenarios():
#     scenarios = get_opportunities()
#     cl.user_session.set("scenarios", scenarios)
#     scenarios = cl.user_session.get("scenarios", None)
#     if scenarios is None:
#         await cl.Message(content="No scenarios found.").send()
#         return
    
#     scenario_actions = []
#     for idx, row in scenarios.iterrows():
#         if row['Opportunity Description'] != "":
#             scenario_action = cl.Action(
#                 name="Scenario",
#                 value=f"{idx}",  # Send the row index as value
#                 description=f"{row['Customer Name']}: {row['Opportunity Name']} ({row['Opportunity Stage']}) "
#                             f"Value: {row['Opportunity Value']}. Meeting with {row['Customer Contact']} "
#                             f"({row['Customer Contact Role']})"
#             )
#             scenario_actions.append(scenario_action)
#     await cl.Message(content="Select a scenario (hover for details):", actions=scenario_actions).send()


async def callback_run_scenario(action):
    await cl.Message(content="*Preparing simulation - please wait ...*").send()
    index = 0
    opportunities = cl.user_session.get("opportunities", None)
    if opportunities is None:
        await cl.Message(content="No scenarios found.").send()
        return
    await cl.Message(content="*Gathering opportunity information ...*").send()
    await asyncio.sleep(1) 

    await cl.Message(content="*Customizing questions for this opportunity ...*").send()  
    await asyncio.sleep(1)

    selected_opportunity = opportunities.iloc[index]
    session_state = cl.user_session.get("session_state", None)
    session_state.add_scenario_info(selected_opportunity) 
    get_customer_background(session_state, selected_opportunity['Customer Name'])
    if session_state.ask_objections:
        print("creating objections")
        session_state.objections = await create_objections(session_state)
        questions = []
        for obj in session_state.objections:
            print(obj)
            q = {"stage": session_state.opportunity.stage, "question": obj[3:], "ground_truth": ""}
            questions.append(q)
        session_state.questions = questions
    else:
        print("questions created")
        session_state.questions = get_questions(session_state.opportunity.stage, session_state.num_questions)
    for q in session_state.questions:
        print(q)
    opening_message = session_state.get_opening()  
    await cl.Message(content=opening_message).send()
    start_actions = [
        cl.Action(name="Start Simulation", value="start_simulation", description="Start Simulation"),
    ]
    await cl.Message(content="Click to start simulation", actions=start_actions).send()


async def callback_start_scenario():
    print("callback_start_scenario()")
    session_state = cl.user_session.get("session_state", None)
    start_time = datetime.now()
    print("setting start time")
    session_state.start_time = start_time
    output = f"{session_state.customer.contact_name} joins the zoom call"
    print(output)
    await cl.Message(content=output).send()

async def callback_evaluate_performance():
    session_state = cl.user_session.get("session_state", None)
    if session_state is None:
        await cl.Message(content="No session found.").send()
        return  
    await display_evaluation_results(cl, session_state)

async def callback_display_queries_responses():
    session_state = cl.user_session.get("session_state", None)
    if session_state is None:
        await cl.Message(content="No session found.").send()
        return  
    await display_llm_responses(cl, session_state)   