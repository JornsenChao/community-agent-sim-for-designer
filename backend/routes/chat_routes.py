from flask import Blueprint, request, jsonify
from services.chat_service import handle_chat

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/ask', methods=['POST'])
def ask():
    data = request.json
    agent_id = data.get('agentId', 'unknown')
    user_message = data.get('message', '')

    response = handle_chat(agent_id, user_message)
    
    return jsonify({"response": response})
