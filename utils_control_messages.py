async def handle_control_message(cl, command):
    command_parts = command.split()
    main_command = command_parts[0].lower()

    if main_command == 'start':
        await cl.Message(content="Starting new session...").send()
    
    elif main_command == 'stop':
        session_state = cl.user_session.get("session_state")
        end_time = datetime.now()
        duration = end_time - session_state.start_time
        duration_minutes = round(duration.total_seconds() / 60)
        session_state.end_time = end_time
        session_state.duration_minutes = duration_minutes
        
        await cl.Message(content=f"Ending current session after {session_state.duration_minutes} minutes").send()
    elif main_command == 'pause':
        await cl.Message(content="Ending current session...").send()

    elif main_command == 'time':
        session_state = cl.user_session.get("session_state")
        duration = session_state.get_session_duration()
        await cl.Message(content=f"Current session duration: {duration}").send()
    
    else:
        await cl.Message(content=f"Unknown command: {main_command}").send()
