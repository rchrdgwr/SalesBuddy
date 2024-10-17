import chainlit as cl
import pandas as pd
from datetime import datetime

async def pose_objections(session_state):
    await cl.AskUserMessage(
            content="Are you ready?", timeout=300
        ).send()
    objection_chain = cl.user_session.get("objection_chain")
    # Retrieve the list of objections
    objections = cl.user_session.get("objections")
    #print (objections[0])
    objection_responses = {}

    # Iterate through each objection
    for i, objection in enumerate(objections):
        # Return the objection in the form of a question
        await cl.Message(content=f"Objection: {objection}").send()

        # Capture user input
        user_response = await cl.AskUserMessage(
            content="How would you respond to this objection?", timeout=600
        ).send()

        objection_responses[objection] = user_response['content']

        # Process the user's response (you can implement your logic here)
        # new_objection_response = generate_response_to_objection(user_response.content)

        # Send the response back to the user
        # await cl.Message(content=f"Response to objection {i + 1}: {new_objection_response}").send()
    print (objection_responses)
    data = []
    for objection, response in objection_responses.items():
        data.append({
            "timestamp": datetime.now(),  # Capture the current timestamp
            "objection": objection,
            "response": response
        })

    # Create a DataFrame
    user_response = pd.DataFrame(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    #r esponse = await generate_response_to_objection(user_response, 0)
    # user_response.to_csv(f'data/user_response_{timestamp}.csv', index=Fals