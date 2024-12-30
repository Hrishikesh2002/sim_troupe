from flask import Flask, render_template, jsonify
import sys
sys.path.append(r"TinyTroupe")
from tinytroupe.openai_utils import OpenAIClient, LLMRequest
import logging
import os

from dotenv import load_dotenv

load_dotenv()


os.environ["OPENAI_API_KEY"] = os.getenv('SECRET_KEY')

# Configure logging
logging.getLogger("tinytroupe").setLevel(logging.WARNING)

app = Flask(__name__)
client = OpenAIClient()

# Workflow definition
WORKFLOW = [
    {
        "stage": "1. Account Created",
        "prompt": "What's the first step after account creation?",
        "next_stage_prompt": "Based on initial account creation data, which verification step should be prioritized?",
        "color": "#2196F3",
        "possible_next": ["2. Email Verification", "3. Phone Verification", "5. Review Process"]
    },
    {
        "stage": "2. Email Verification",
        "prompt": "What happens during email verification?",
        "next_stage_prompt": "Given the verification result, what should be the next step?",
        "color": "#00BCD4",
        "possible_next": ["3. Phone Verification", "5. Review Process", "4. KYC Documents", "9. Closed"]
    },
    {
        "stage": "3. Phone Verification",
        "prompt": "What happens during phone verification?",
        "next_stage_prompt": "Based on verification outcome, what's the appropriate next step?",
        "color": "#FFEB3B",
        "possible_next": ["2. Email Verification", "4. KYC Documents", "5. Review Process", "9. Closed"]
    },
    {
        "stage": "4. KYC Documents",
        "prompt": "What happens during KYC document processing?",
        "next_stage_prompt": "Based on submitted documents, where should this account go?",
        "color": "#FF9800",
        "possible_next": ["5. Review Process", "3. Phone Verification", "9. Closed"]
    },
    {
        "stage": "5. Review Process",
        "prompt": "What checks happen during review?",
        "next_stage_prompt": "Given the findings, what should be the next stage?",
        "color": "#E91E63",
        "possible_next": ["6. Activated", "4. KYC Documents", "3. Phone Verification", "2. Email Verification", "9. Closed"]
    },
    {
        "stage": "6. Activated",
        "prompt": "What features become available upon activation?",
        "next_stage_prompt": "Based on initial activity patterns, what monitoring state is appropriate?",
        "color": "#4CAF50",
        "possible_next": ["7. Active Usage", "5. Review Process", "8. Dormant"]
    },
    {
        "stage": "7. Active Usage",
        "prompt": "What monitoring happens during usage?",
        "next_stage_prompt": "Given recent activity patterns, should the status change?",
        "color": "#8BC34A",
        "possible_next": ["8. Dormant", "5. Review Process", "9. Closed"]
    },
    {
        "stage": "8. Dormant",
        "prompt": "What triggers dormant status?",
        "next_stage_prompt": "Based on dormancy duration, what should happen to this account?",
        "color": "#9E9E9E",
        "possible_next": ["7. Active Usage", "5. Review Process", "9. Closed"]
    },
    {
        "stage": "9. Closed",
        "prompt": "What are the final steps in account closure?",
        "next_stage_prompt": None,
        "color": "#F44336",
        "possible_next": []
    }
]

@app.route('/')
def index():
    return render_template('index.html', workflow=WORKFLOW)

@app.route('/api/next_stage/<int:current_stage>')
def get_next_stage(current_stage):
    if current_stage >= len(WORKFLOW) or not WORKFLOW[current_stage]["possible_next"]:
        return jsonify({"next_stage": None, "reason": "No possible next stage.", "sentiment": "neutral"})
    
    try:
        current = WORKFLOW[current_stage]

        # Request AI to determine next stage, provide a reason, and sentiment
        llm_request = LLMRequest(
            system_prompt=f"""You are a financial compliance AI making decisions about account workflow routing.
            Current stage: {current['stage']}
            Possible next stages: {', '.join(current['possible_next'])} \n
            ignore the numbering of the stages and focus on the stage name.
            
            Consider regulatory requirements, risk factors, and business priorities.
            Respond strictly in the format: Stage Name || Reason for decision || Sentiment.
            Example: 2. Email Verification || Email verification is prioritized due to compliance needs || Positive""",
            user_prompt=current["next_stage_prompt"]
        )

        # Fetch AI response and handle parsing
        llm_response = llm_request.call().strip()
        logging.debug(f"AI Response for stage {current['stage']}: {llm_response}")

        # Split response using '||' separator
        parts = llm_response.split('||')
        if len(parts) != 3:
            logging.error(f"Malformed AI response: {llm_response}")
            raise ValueError("Malformed AI response. Expected 'Stage Name || Reason || Sentiment'")

        next_stage_name = parts[0].strip()
        reason = parts[1].strip()
        sentiment = parts[2].strip().lower()

        # Validate and find index of next stage
        for idx, stage in enumerate(WORKFLOW):
            if stage["stage"] == next_stage_name and next_stage_name in current["possible_next"]:
                return jsonify({
                    "next_stage": idx,
                    "stage_name": next_stage_name,
                    "reason": reason,
                    "sentiment": sentiment,
                    "decision": f"Moving to {next_stage_name} based on compliance analysis."
                })

        # Log and handle fallback
        logging.warning(f"AI returned an invalid next stage: {next_stage_name}")
        fallback_stage = current["possible_next"][0]
        for idx, stage in enumerate(WORKFLOW):
            if stage["stage"] == fallback_stage:
                return jsonify({
                    "next_stage": idx,
                    "stage_name": fallback_stage,
                    "reason": f"Fallback to {fallback_stage} due to: {llm_response}.",
                    "sentiment": "neutral",
                    "decision": "Routing to fallback stage."
                })

    except Exception as e:
        logging.error(f"Error determining next stage: {e}")
        return jsonify({
            "error": str(e),
            "next_stage": None,
            "reason": "An error occurred during decision-making. Please try again.",
            "sentiment": "neutral"
        })

    # Default response if all else fails
    return jsonify({
        "next_stage": None,
        "reason": "Unable to determine next stage due to unexpected error.",
        "sentiment": "neutral",
        "decision": "Routing failed."
    })



if __name__ == '__main__':
    app.run(debug=True)