import os
import sys
import signal
from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
sys.path.append('TinyTroupe')

load_dotenv()


os.environ["OPENAI_API_KEY"] = os.getenv('SECRET_KEY')
# for tinytroupe to work, install:  rich, chevron, pydantic, llama-index, llama-index-readers-web

import random
import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.factory import TinyPersonFactory

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize the TinyPersonFactory

default_template = """People with a broad and diverse range of personalities, interests, backgrounds and socioeconomic status.
                Focus in particular:
              - on financial aspects, ensuring we have both people with high and low income.
              - on aesthetic aspects, ensuring we have people with different tastes."""
              
factory = TinyPersonFactory(default_template)

# Generate the specified number of personas
count = 3
people = factory.generate_people(count, "A random person from the target audience",
                                    temperature=1.9,
                                    verbose=True)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_personas', methods=['GET'])
def generate_personas():
    try:
        # Convert the personas to a JSON-serializable format
        personas = []
        for person in people:
            persona_dict = {
                'name': person.name if hasattr(person, 'name') else "Unknown",
                'bio': person.minibio(),
            }
            personas.append(persona_dict)
            
        print("c")
        
        # Return the personas as JSON
        return jsonify({'personas': personas})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200


def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    # Perform any cleanup here if needed
    sys.exit(0)



if __name__ == '__main__':
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the Flask app
    try:
        app.run(debug=True, use_reloader=False, port=2846)
    except SystemExit:
        print('Flask application has been shut down.')