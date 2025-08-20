import google.generativeai as genai

# Configure with your API key
API_KEY = "AIzaSyCvnsxyM7yefjnFOGJpHkFzqxB7BHzpo20"
genai.configure(api_key=API_KEY)

# Create the model (Gemini Pro is used here)
model = genai.GenerativeModel('gemini-pro')

# Start a chat session (optional but useful for multi-turn memory)
chat = model.start_chat()

print("💬 Ask anything (type 'exit' to quit)\n")

# Main input loop
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Exiting chat.")
        break
    try:
        response = chat.send_message(user_input)
        print("AI:", response.text.strip())
    except Exception as e:
        print("⚠️ Error:", e)
