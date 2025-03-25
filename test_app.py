# Add this code temporarily to check the actual API
import inspect
from elevenlabs.conversational_ai.conversation import Conversation

print("Conversation parameters:")
print(inspect.signature(Conversation.__init__))