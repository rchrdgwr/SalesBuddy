import chainlit as cl

async def offer_actions():
    actions = [
        cl.Action(name="Get Latest News on this Customer", value="HSBC", description="Get Latest News"),
        cl.Action(name="Enter Meeting Simulation", value="enter-meeting-simulation", description="Enter Meeting Simulation"),
        cl.Action(name="Review Another Opportunity", value="review-another-opportunity", description="Review Another Opportunity"),
    ]
    await cl.Message(content="Select an action", actions=actions).send()

