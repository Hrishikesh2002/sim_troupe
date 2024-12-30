from flask import Flask, render_template, jsonify, request, send_from_directory
import logging
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import random
import asyncio

load_dotenv()
client = OpenAI(api_key=os.getenv("SECRET_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Lead management workflow definition
WORKFLOW = [
    {
        "stage": "Begun Desk",
        "prompt": "How should we process this new incoming lead?",
        "next_stage_prompt": "Based on the lead details, what's the next appropriate step?",
        "color": "#2196F3",
        "possible_next": ["Assign Desk"]
    },
    {
        "stage": "Assign Desk",
        "prompt": "Which employee should be assigned to this lead?",
        "next_stage_prompt": "Once the lead is assigned, what's the next step?",
        "color": "#00BCD4",
        "possible_next": ["Calling Desk", "Ended Desk"]
    },
    {
        "stage": "Calling Desk",
        "prompt": "How should we approach the call with this lead?",
        "next_stage_prompt": "Based on the call outcome, where should this lead go?",
        "color": "#FFEB3B",
        "possible_next": ["Meeting Desk", "Assign Desk", "Ended Desk"]
    },
    {
        "stage": "Meeting Desk",
        "prompt": "What's the status of the meeting with this lead?",
        "next_stage_prompt": "Based on the meeting outcome, what's the next step?",
        "color": "#FF9800",
        "possible_next": ["Onboarding Desk", "Ended Desk"]
    },
    {
        "stage": "Onboarding Desk",
        "prompt": "What onboarding steps are needed for this closed deal?",
        "next_stage_prompt": "Based on the onboarding status, where should this lead go?",
        "color": "#4CAF50",
        "possible_next": ["Ended Desk"]
    },
    {
        "stage": "Ended Desk",
        "prompt": "What is the final status of this lead?",
        "next_stage_prompt": None,
        "color": "#F44336",
        "possible_next": []
    }
]

# Client products/services for which leads are being collected
CLIENTS = [
    {
        "name": "TechCloud Solutions",
        "product": "Cloud Storage Service",
        "target_market": "Small to Medium Businesses",
        "price_range": "$50-500/month"
    },
    {
        "name": "SecureNet",
        "product": "Cybersecurity Suite",
        "target_market": "Enterprise",
        "price_range": "$1000-5000/month"
    },
    {
        "name": "DataFlow Analytics",
        "product": "Business Intelligence Tools",
        "target_market": "Mid-market Companies",
        "price_range": "$200-2000/month"
    }
]

# Social media platforms (streams) where leads are collected
STREAMS = ["LinkedIn", "Twitter", "Facebook", "Industry Forums", "Email Campaigns"]

# Sample employees who can be assigned to leads
EMPLOYEES = [
    {"name": "Alice Smith", "expertise": ["Cloud Services", "Data Analytics"]},
    {"name": "Bob Johnson", "expertise": ["Cybersecurity", "Enterprise Solutions"]},
    {"name": "Carol Williams", "expertise": ["Business Intelligence", "Consulting"]}
]

class Lead:
    def __init__(self, source_stream):
        self.client = random.choice(CLIENTS)
        self.stream = source_stream
        self.status = {
            "assigned_employee": None,
            "meeting_scheduled": False,
            "meeting_completed": False,
            "deal_status": None,  # can be "closed", "lost", or None
            "onboarding_status": None  # can be "complete", "failed", or None
        }
        self.current_stage = "Begun Desk"
        self.conversation_history = []

    async def respond(self, message):
        prompt = f"""
        You are a lead interested in {self.client['product']} from {self.client['name']}.
        You were found through {self.stream}.
        Current stage: {self.current_stage}
        Status: {self.status}
        
        Previous conversation:
        {self.conversation_history}
        
        Current message: {message}
        
        Respond naturally as this lead, considering your interest in the product and current stage in the process.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        self.conversation_history.append(f"Lead: {response.choices[0].message.content}")
        return response.choices[0].message.content

class LeadAgent:
    def __init__(self, stage):
        self.stage = stage
        self.workflow = next(w for w in WORKFLOW if w["stage"] == stage)

    async def respond(self, message, lead):
        prompt = f"""
        You are a lead management agent at the {self.stage}.
        Current lead details:
        - Interested in: {lead.client['product']}
        - Source: {lead.stream}
        - Status: {lead.status}
        
        Your task: {self.workflow['prompt']}
        
        Current message: {message}
        
        Respond professionally as a lead management agent, following the workflow guidelines for your desk.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        return response.choices[0].message.content

class LeadManagementSystem:
    def __init__(self):
        self.leads = {}
        self.agents = {stage["stage"]: LeadAgent(stage["stage"]) for stage in WORKFLOW}
        
    async def create_lead(self, stream=None):
        if stream is None:
            stream = random.choice(STREAMS)
            
        lead = Lead(stream)
        lead_id = f"LEAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.leads[lead_id] = lead
        return lead_id, lead

    async def process_lead(self, lead_id):
        lead = self.leads[lead_id]
        current_agent = self.agents[lead.current_stage]
        
        # Process the lead based on current stage
        conversation = []
        next_stage = None
        
        # Generate appropriate response based on stage
        agent_message = await current_agent.respond("", lead)
        conversation.append({"role": "agent", "content": agent_message})
        
        # Update lead status based on stage
        if lead.current_stage == "Assign Desk" and not lead.status["assigned_employee"]:
            lead.status["assigned_employee"] = random.choice(EMPLOYEES)["name"]
        elif lead.current_stage == "Meeting Desk":
            if not lead.status["meeting_completed"]:
                lead.status["meeting_completed"] = True
                lead.status["deal_status"] = random.choice(["closed", "lost"])
        elif lead.current_stage == "Onboarding Desk" and lead.status["deal_status"] == "closed":
            lead.status["onboarding_status"] = random.choice(["complete", "failed"])
        
        # Determine next stage based on status
        next_stage = await self.determine_next_stage(lead, current_agent)
        if next_stage:
            lead.current_stage = next_stage
            
        return {
            "conversation": conversation,
            "next_stage": next_stage,
            "status": lead.status
        }

    async def determine_next_stage(self, lead, current_agent):
        # Logic for determining next stage based on lead status
        if lead.current_stage == "Begun Desk":
            return "Assign Desk"
        elif lead.current_stage == "Assign Desk":
            return "Calling Desk" if lead.status["assigned_employee"] else "Ended Desk"
        elif lead.current_stage == "Calling Desk":
            return "Meeting Desk" if not lead.status["meeting_completed"] else "Assign Desk"
        elif lead.current_stage == "Meeting Desk":
            if lead.status["deal_status"] == "closed":
                return "Onboarding Desk"
            else:
                return "Ended Desk"
        elif lead.current_stage == "Onboarding Desk":
            return "Ended Desk"
        return None

system = LeadManagementSystem()

@app.route('/create_lead', methods=['POST', 'GET'])  # Added GET for testing
def create_lead():
    try:
        # Try to get stream from JSON if it exists
        if request.is_json:
            stream = request.json.get('stream')
        # Otherwise try to get it from form data or query parameters
        else:
            stream = request.form.get('stream') or request.args.get('stream')
        
        lead_id, lead = asyncio.run(system.create_lead(stream))
        return jsonify({
            "lead_id": lead_id,
            "client": lead.client,
            "stream": lead.stream,
            "status": lead.status
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to create lead"
        }), 500
        


@app.route('/process_lead/<lead_id>', methods=['POST'])
def process_lead(lead_id):
    result = asyncio.run(system.process_lead(lead_id))
    return jsonify(result)

@app.route('/')
def index():
    return send_from_directory('./templates', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3847)