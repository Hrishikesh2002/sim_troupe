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

# Marketing firm workflow definition
WORKFLOW = [
    {
        "stage": "Begun Desk",
        "prompt": "How should we handle this new incoming lead?",
        "next_stage_prompt": "Based on the incoming lead details, what's the next appropriate step?",
        "color": "#2196F3",
        "possible_next": ["Assign Desk"]
    },
    {
        "stage": "Assign Desk",
        "prompt": "How should we assign this lead?",
        "next_stage_prompt": "Given the lead's requirements and team availability, what should happen next?",
        "color": "#00BCD4",
        "possible_next": ["Calling Desk", "Ended Desk"]
    },
    {
        "stage": "Calling Desk",
        "prompt": "What's the next step in the calling process?",
        "next_stage_prompt": "Based on the call outcome, where should this lead go?",
        "color": "#FFEB3B",
        "possible_next": ["Meeting Desk", "Assign Desk", "Ended Desk"]
    },
    {
        "stage": "Meeting Desk",
        "prompt": "How should we prepare for this meeting?",
        "next_stage_prompt": "Based on the meeting results, what's the next step?",
        "color": "#FF9800",
        "possible_next": ["Onboarding Desk", "Assign Desk", "Ended Desk"]
    },
    {
        "stage": "Onboarding Desk",
        "prompt": "What onboarding steps are needed?",
        "next_stage_prompt": "Based on the onboarding progress, where should this lead go?",
        "color": "#4CAF50",
        "possible_next": ["Ended Desk"]
    },
    {
        "stage": "Ended Desk",
        "prompt": "What final steps are needed?",
        "next_stage_prompt": None,
        "color": "#F44336",
        "possible_next": []
    }
]

# Lead profiles for simulation
LEAD_PROFILES = [
    {
        "name": "Tech Startup Lead",
        "company": "InnovateTech",
        "interest": "Digital Marketing Services",
        "budget": "50000-100000",
        "urgency": "High"
    },
    {
        "name": "Retail Business Lead",
        "company": "ShopLocal",
        "interest": "Social Media Marketing",
        "budget": "10000-25000",
        "urgency": "Medium"
    },
    {
        "name": "Enterprise Lead",
        "company": "MegaCorp",
        "interest": "Full-Service Marketing",
        "budget": "200000+",
        "urgency": "Low"
    }
]


class MarketingLead:
    def __init__(self, profile):
        self.name = profile["name"]
        self.profile = profile
        self.current_stage = "Begun Desk"
        self.conversation_history = []

    async def respond(self, message):
        prompt = f"""
        You are {self.profile['name']} from {self.profile['company']}.
        You are interested in {self.profile['interest']}.
        Your budget range is {self.profile['budget']}.
        Your urgency level is {self.profile['urgency']}.
        
        Previous conversation:
        {self.conversation_history}
        
        Current message: {message}
        
        Respond naturally as this lead, keeping in mind your profile and previous interactions.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        self.conversation_history.append(f"Lead: {response.choices[0].message.content}")
        return response.choices[0].message.content

class MarketingDesk:
    def __init__(self, stage):
        self.name = f"{stage} Agent"
        self.stage = stage
        self.workflow = next(w for w in WORKFLOW if w["stage"] == stage)

    async def respond(self, message, lead_profile):
        prompt = f"""
        You are a marketing firm agent at the {self.stage}.
        Current lead profile:
        {lead_profile}
        
        Your task: {self.workflow['prompt']}
        
        Current message: {message}
        
        Respond professionally as a marketing agent, following the workflow guidelines for your desk.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        return response.choices[0].message.content

class MarketingSimulation:
    def __init__(self):
        self.leads = {}
        self.desks = {stage["stage"]: MarketingDesk(stage["stage"]) for stage in WORKFLOW}
        
    async def create_lead(self, profile_type="random"):
        if profile_type == "random":
            profile = random.choice(LEAD_PROFILES)
        else:
            profile = next(p for p in LEAD_PROFILES if p["name"] == profile_type)
            
        lead = MarketingLead(profile)
        self.leads[lead.name] = lead
        return lead

    async def process_lead(self, lead_name):
        lead = self.leads[lead_name]
        current_desk = self.desks[lead.current_stage]
        
        # Start conversation
        conversation = []
        
        # Initial message from desk
        initial_message = await current_desk.respond("", lead.profile)
        conversation.append({"role": "agent", "content": initial_message})
        
        # Lead response
        lead_response = await lead.respond(initial_message)
        conversation.append({"role": "lead", "content": lead_response})
        
        # Determine next stage
        next_stage = await self.determine_next_stage(lead, current_desk)
        if next_stage:
            lead.current_stage = next_stage
            
        return {
            "conversation": conversation,
            "next_stage": next_stage
        }

    async def determine_next_stage(self, lead, current_desk):
        prompt = f"""
        Based on the lead profile and conversation history, determine the next appropriate stage.
        Current stage: {current_desk.stage}
        Possible next stages: {current_desk.workflow['possible_next']}
        Lead profile: {lead.profile}
        Conversation history: {lead.conversation_history}
        
        Return only the name of the next stage.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        
        next_stage = response.choices[0].message.content.strip()
        if next_stage in current_desk.workflow['possible_next']:
            return next_stage
        return None

simulation = MarketingSimulation()

@app.route('/create_lead', methods=['POST'])
def create_lead():
    lead = asyncio.run(simulation.create_lead())
    return jsonify({"lead_name": lead.name, "profile": lead.profile})

@app.route('/process_lead/<lead_name>', methods=['POST'])
def process_lead(lead_name):
    result = asyncio.run(simulation.process_lead(lead_name))
    return jsonify(result)

@app.route('/')
def index():
    return send_from_directory('./templates', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=3847)