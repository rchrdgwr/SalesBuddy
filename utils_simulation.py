import asyncio
import json
import chainlit as cl
from datetime import datetime
from utils_chain_parameters import prepare_chain_parameters
from utils_output import display_evaluation_results 
from utils_voice import reply_with_voice


async def do_simulation(client, session_state, message):
    if session_state.status == "active":
        chain = cl.user_session.get("chain")
        history = cl.user_session.get("history", [])
        history.append({"role": "user", "content": message})
        session_state.previous_answer = message.content
        prompt_parm = prepare_chain_parameters(session_state, message, history)
        session_state.queries.append(prompt_parm)
        response_content = chain.invoke(prompt_parm)
        json_str = response_content.content.strip('```json\n').strip('```')
        try:
            this_response = json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(response_content.content)
            print(f"Error at position {e.pos}: {json_str[max(0, e.pos-10):e.pos+10]}")
            this_response = {"Response": "Error receiving response from LLM"}  
        llm_response = this_response.get("Response", "No response from LLM")
        print("LLM Response:")
        print(llm_response)
        session_state.llm_responses.append(this_response)
        print("Next question:")
        print(this_response.get("Question", "No question"))

        if session_state.question != "":
            session_state.responses.append({
                "question_number": session_state.current_question_index,
                "question": session_state.question,
                "response": session_state.rep_answer,
                "ground_truth": session_state.ground_truth,
                "response_score": this_response.get("Score", "No score"),
                "response_evaluation": this_response.get("Evaluation", "No evaluation"),
                "mood_score": this_response.get("Mood Score", "No mood score"),
                "overall_score": this_response.get("Overall Score", "No overall score"),
                "overall_evaluation": this_response.get("Overall Evaluation", "No overall evaluation"),
            })
        message_to_rep = llm_response + "\n\n" + this_response.get("Question", "No question")
        print("Checking to continue")
        print(session_state.current_question_index)
        print(len(session_state.questions))
        if session_state.current_question_index < len(session_state.questions):
            if session_state.do_voice:
                await reply_with_voice(cl, client, message_to_rep)
            else:
                await cl.Message(content=message_to_rep, author="John Smith").send()
            # await cl.Message(this_response).send()
            history.append({"role": "assistant", "content": response_content})
            cl.user_session.set("history", history)
            session_state.current_question_index += 1
        else:
            final_message = message_to_rep
            conclusion = this_response.get("Conclusion", "")
            if conclusion != "":
                final_message = final_message + "\n\n" + conclusion
            if session_state.do_voice:
                await reply_with_voice(cl, client, final_message)
            else:
                await cl.Message(message_to_rep).send()
            session_state.status = "complete"
            end_time = datetime.now()
            session_state.end_time = end_time
            if session_state.start_time:
                try:
                    duration = end_time - session_state.start_time
                    duration_minutes = round(duration.total_seconds() / 60)
                except:
                    print("Error calculating duration")
                    duration = 130
                    duration_minutes = 2
                    
            session_state.duration_minutes = duration_minutes   
            if session_state.do_evaluation:
                await display_evaluation_results(cl, session_state)
            else:
                await cl.Message(content="**Simulation Complete**").send()
                evaluate_actions = [
                    cl.Action(name="Evaluate Performance", value="evaluate", description="Evaluate Performance"),
                    cl.Action(name="Display Queries and Responses", value="display_llm_responses", description="Display LLM Responses")
                ]
                await cl.Message(content="Click to evaluate performance", actions=evaluate_actions).send()
                await cl.Message(content="\n\n").send()