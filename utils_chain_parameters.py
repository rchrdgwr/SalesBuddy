def prepare_chain_parameters(session_state, message, history):
    message = message.content
    previous_question = ""
    rep_answer = ""
    next_question = ""  
    ground_truth = ""
    command = ""
    print(f"Index: {session_state.current_question_index}")
    if session_state.current_question_index == 0:
        previous_question = ""
        rep_answer = ""
        ground_truth = ""
        next_question = session_state.questions[session_state.current_question_index]["question"]
        command = "You should greet the rep"
    elif session_state.current_question_index >= len(session_state.questions):
        next_question = "" 
        previous_question = session_state.questions[session_state.current_question_index - 1]["question"]
        rep_answer = session_state.previous_answer
        ground_truth = session_state.questions[session_state.current_question_index - 1]["ground_truth"]
        command = """Thank the customer, offer a comment on the answer and overall performance.
            Conclude the conversation with a summary and give a farewell. 
            You can add additional comments as needed.
        """
    else:
        previous_question = session_state.questions[session_state.current_question_index - 1]["question"]
        rep_answer = session_state.previous_answer
        next_question = session_state.questions[session_state.current_question_index]["question"]
        ground_truth = session_state.questions[session_state.current_question_index]["ground_truth"]
        command = "You should respond to the answer based on how well the rep answered the previous question."
    session_state.ground_truth = ground_truth
    session_state.question = previous_question
    session_state.rep_answer = rep_answer
    print("--------------------------------")
    print(f"Message: {message}")
    print("Sending the following:")
    print(f"Command: {command}")
    print(f"Previous question: {previous_question}")
    print(f"Rep answer: {rep_answer}")
    print(f"Next question: {next_question}")

    rep_company_details = f"""
        Name: {session_state.company.name}
        Description: {session_state.company.description}
        Product: {session_state.company.product}
        Product Summary: {session_state.company.product_summary}
        Product Description: {session_state.company.product_description}
    """
    company_details = f"""
        Name: {session_state.customer.name}
        Description: {session_state.customer.background}
    """
    scenario = f"""
        Opportunity Name: {session_state.opportunity.name}
        Opportunity Description: {session_state.opportunity.description} 
        Opportunity Stage: {session_state.opportunity.stage}
        Opportunity Value: {session_state.opportunity.value}
        Opportunity Close Date: {session_state.opportunity.close_date}   
    """
    parm = {"conversation_mode": session_state.qa_mode,
            "message": message,
            "name": session_state.customer.contact_name,
            "company": company_details,
            "role": session_state.customer.contact_role,
            "sales_rep": "Tony Snell",
            "rep_company": rep_company_details,
            "attitude": session_state.attitude,
            "mood_score": session_state.mood_score,
            "scenario": scenario,
            "stage": session_state.opportunity.stage, 
            "previous_question": previous_question,
            "next_question": next_question, 
            "rep_answer": rep_answer,   
            "conversation_history": history,   
            "command": command,
            }
    return parm

