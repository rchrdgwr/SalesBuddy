import asyncio
import chainlit as cl
import os
from langchain_openai import ChatOpenAI

from utils_actions import offer_actions,offer_initial_actions
from utils_customer_research import read_markdown_file
from utils_data import get_company_data, get_opportunities
from utils_objections import create_objections
from utils_opportunity_review import prep_opportunity_review
from utils_prompt import get_chat_prompt

async def prep_start(session_state):

    get_company_data(session_state)
    chat_prompt = get_chat_prompt()
    chat_model = ChatOpenAI(model=session_state.llm_model)
    simple_chain = chat_prompt | chat_model
    cl.user_session.set("chain", simple_chain)

    welcome_message = f"**Welcome to {session_state.company.name} SalesBuddy**\n*Your AI assistant for sales and sales management*"
    await cl.Message(content=welcome_message).send()
    # await cl.Message(content=session_state.company.product_summary).send()

    image = cl.Image(path="images/salesbuddy_logo.jpg", name="salesbuddy_logo", display="inline")
    await cl.Message(
        content=" ",
        elements=[image],
    ).send()

    await offer_initial_actions()


    opportunities = get_opportunities()
    cl.user_session.set("opportunities", opportunities)

async def prep_opportunities(session_state):

    research_title = "**Upcoming Opportunities**"
    await cl.Message(content=research_title).send()
    opportunities = cl.user_session.get("opportunities", None)
    if opportunities is None:
        await cl.Message(content="No scenarios found.").send()
        return
    opportunity_actions = []
    for idx, row in opportunities.iterrows():
        if row['Opportunity Description'] != "":
            customer_name = row['Customer Name']
            opportunity_name = row['Opportunity Name']
            opportunity_stage = row['Opportunity Stage']
            name = f"{customer_name}: {opportunity_name} ({opportunity_stage})"
            opportunity_action = cl.Action(
                name=name,
                value=f"{idx}",  # Send the row index as value
                description=f"{row['Customer Name']}: {row['Opportunity Name']} ({row['Opportunity Stage']}) "
                            f"Value: {row['Opportunity Value']}. Meeting with {row['Customer Contact']} "
                            f"({row['Customer Contact Role']})"
            )
            opportunity_actions.append(opportunity_action)
    await cl.Message(content="Select an opportunity (hover for details):", actions=opportunity_actions).send()

async def prep_opportunity_analysis():

    session_state = cl.user_session.get("session_state", None)
    opportunity_analysis_message = "Reviewing HSBC Opportunitiy - please wait..."
    await cl.Message(content=opportunity_analysis_message).send()
    
    if session_state.do_opportunity_analysis:
        agent_1_message = "*Retrieving and evaluating opportunity data from SalesForce CRM ...*"
        await cl.Message(content=agent_1_message).send()
        await prep_opportunity_review(session_state)
        report = session_state.opportunity_review_report
        await cl.Message(content=report).send()
    else:

        agent_1_message = "*Retrieving data from SalesForce CRM ...*"
        await cl.Message(content=agent_1_message).send()
        await asyncio.sleep(2)

        if session_state.add_objections_to_analysis:
            agent_3_message = "*Evaluating opportunity data and identifying risks ...*"
            await cl.Message(content=agent_3_message).send()
            session_state.objections = await create_objections(session_state)
        else:
            agent_2_message = "*Evaluating opportunity data...*"
            await cl.Message(content=agent_2_message).send()
            await asyncio.sleep(1.5)

        agent_3_message = "*Determining next steps ...*"
        await cl.Message(content=agent_3_message).send()
        await asyncio.sleep(1)
        output_message = "**Analysis Results**"
        await cl.Message(content=output_message).send()

        markdown_file_path = "reports/HSBC Opportunity Review Report.md"
        if os.path.exists(markdown_file_path):
            await cl.Message(content=read_markdown_file(markdown_file_path)).send() 
        else:
            output_messages = get_opportunity_analysis()
            for output_message in output_messages:  
                await cl.Message(content=output_message).send()
                await cl.Message(content="").send() 

            if session_state.add_objections_to_analysis:
                output_message = "**Risks**"
                await cl.Message(content=output_message).send()
                for obj in session_state.objections:
                    await cl.Message(content=obj).send()

            output_message = "**Next Steps**"
            await cl.Message(content=output_message).send()
            output_messages = get_next_steps()
            for output_message in output_messages:  
                await cl.Message(content=output_message).send()
                await cl.Message(content="").send() 
            await cl.Message(content="\n\n").send()

    await offer_actions()

async def prep_research(session_state):
    research_title = "**Customer Research**"
    await cl.Message(content=research_title).send()
    research_message = "Enter customer name to research"
    await cl.Message(content=research_message).send()


def get_opportunity_analysis():
    output_1 = "**Summary:** The HSBC opportunity involves replacing the existing analytics engine for their loan origination system, valued at $250,000. The current system is slow and lacks flexibility, creating urgency due to an impending renewal with the existing vendor. Multiple meetings have been conducted, culminating in a proposal review. The decision process is progressing, with a meeting scheduled on October 26 with John Smith to discuss the next steps. Potential for pilot program or final negotiations."
    output_2 = "**Score: 75**"
    output_3 = "**MEDDIC Evaluation:**" 
    output_4 = "**Metrics: 70** - The proposal discussed expected performance improvements and ROI, but specific quantitative metrics driving the decision were not detailed."
    output_5 = "**Economic Buyer: 65** - There is no direct mention of engagement with the ultimate economic buyer, although the CFO's involvement in the proposal review suggests some level of engagement."
    output_6 = "**Decision Criteria: 75** - The decision criteria seem to be partially understood, as there has been discussion about ROI, performance improvements, and contract terms, but further clarity is needed."
    output_7 = "**Decision Process: 80** - The decision process appears to be well-understood, with clear next steps and urgency due to the vendor renewal timeline."
    output_8 = "**Identify Pain: 85** - The pain points related to the existing system's performance and flexibility are clearly identified, driving the opportunity forward."
    output_9 = "**Champion: 75** - John Smith, the VP of IT, appears to be a potential champion, as he is involved in every meeting, but his level of influence and commitment is not fully confirmed."
    outputs = [output_1, output_2, output_3, output_4, output_5, output_6, output_7, output_8, output_9]
    return outputs
def get_next_steps():
    output_10 = "Engage with the CFO and other key stakeholders to refine the understanding of the decision criteria and ensure alignment with their expectations. Confirm John Smith's role as a champion and clarify his influence on the decision-making process."
    output_11 = "**Talking Points:**"
    output_12 = "    1. Discuss specific quantitative metrics and performance benchmarks that demonstrate the expected improvements and ROI to solidify the business case"
    output_13 = "    2. Address the decision criteria with more clarity, ensuring that all stakeholders, including the CFO, have a shared understanding of what is needed to move forward"
    output_14 = "    3. Highlight the urgency of the situation due to the impending vendor renewal and how your solution can address the identified pain points in a timely manner"
    outputs = [output_10, output_11, output_12, output_13, output_14]
    return outputs


async def prep_latest_news():
    latest_news_message = "Retrieving latest news on this customer - please wait..."
    await cl.Message(content=latest_news_message).send()
    await asyncio.sleep(2)
    agent_1_message = "Agent 1: Processing data..."
    await cl.Message(content=agent_1_message).send()
    await asyncio.sleep(1)
    agent_2_message = "Agent 2: Evaluating opportunity..."
    await cl.Message(content=agent_2_message).send()