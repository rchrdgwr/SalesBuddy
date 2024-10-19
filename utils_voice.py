import os

async def reply_with_voice(cl,client, assistant_message):

    try:
        speech_file_path = "response.mp3"
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=assistant_message
        )
        
        with open(speech_file_path, "wb") as file:
            file.write(response.content)

        # Send audio file to user
        elements = [
            cl.Audio(name="Voice", path=speech_file_path, display="inline")
        ]
        await cl.Message(content=assistant_message, elements=elements, author="John Smith").send()
    except Exception as e:
        await cl.Message(content=f"Error generating or sending audio: {e}").send()
    finally:
        if os.path.exists(speech_file_path):
            os.remove(speech_file_path)
        return
