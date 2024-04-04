def get_gemini_response(question):
    model = genai.GenerativeModel("gemini-pro") 
    chat = model.start_chat(history=[])
    response = chat.send_message(question, stream=True)
    response_text = ''
    for chunk in response:
        if hasattr(chunk, 'text'):
            response_text += chunk.text
    return response_text
