import chainlit as cl

async def offer_initial_actions():
    actions = [
        cl.Action(name="Deal Analysis", value="deal-analysis", description="Deal Analysis"),
        cl.Action(name="Customer Research", value="customer-research", description="Customer Research"),
        cl.Action(name="Sales Simulation", value="sales-simulation", description="Sales Simulation"),
    ]
    await cl.Message(content=" ", actions=actions).send()
    await cl.Message(content="\n\n").send()

async def offer_actions():
    await cl.Message(content="\n\n").send()
    actions = [
        cl.Action(name="Get Latest News on this Customer", value="HSBC", description="Get Latest News"),
        cl.Action(name="Enter Meeting Simulation", value="enter-meeting-simulation", description="Enter Meeting Simulation"),
        cl.Action(name="Review Another Opportunity", value="review-another-opportunity", description="Review Another Opportunity"),
    ]
    await cl.Message(content="Select an action", actions=actions).send()
    await cl.Message(content="\n\n").send()

