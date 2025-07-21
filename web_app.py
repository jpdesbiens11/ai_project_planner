from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import json
import logging
import pandas as pd
import subprocess
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Try to import your AI service
try:
    from models.ai_service import AIService
    logger.info("Successfully imported AIService")
except ImportError as e:
    logger.error(f"Error importing AIService: {str(e)}")
    
    # Create a dummy AIService for testing if import fails
    class AIService:
        def __init__(self, model_name="dummy", api_url="http://localhost:11434/api/generate"):
            self.model = model_name
            self.api_url = api_url
            logger.info(f"Initialized dummy AIService with model: {model_name}")
        
        def ask_question(self, prompt, tasks=None):
            return f"This is a test response from {self.model}. You asked: {prompt}"
        
        def ask_question_with_csv(self, prompt, csv_path):
            try:
                # Construct a command to run Ollama CLI
                cmd = ["ollama", "run", self.model, f"CSV file: {csv_path}\n\nQuestion: {prompt}"]
                
                # Run the command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Get the output
                if result.returncode == 0:
                    return result.stdout
                else:
                    error_msg = f"Error running Ollama CLI: {result.stderr}"
                    logger.error(error_msg)
                    return f"Error: {error_msg}"
            except Exception as e:
                logger.error(f"Exception running Ollama CLI: {str(e)}")
                return f"Error: {str(e)}"

# Initialize Flask application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates for development

# Configure the available models based on Ollama
def get_available_models():
    try:
        # Use subprocess to get models from Ollama CLI
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header line
                models = []
                for line in lines[1:]:
                    if line.strip():
                        # Extract model name (first column)
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
        # Fallback
        return ["llama3", "mistral", "gemma"]
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return ["llama3", "mistral", "gemma"]

@app.route('/')
def index():
    models = get_available_models()
    return render_template('index.html', models=models)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    selected_model = data.get('model', 'llama3')
    csv_data = data.get('csvData')
    csv_filename = data.get('csvFilename')
    
    try:
        # Initialize the AI service
        ai_service = AIService(model_name=selected_model, api_url="http://localhost:11434/api/generate")
        
        # Handle CSV data if available
        if csv_data and len(csv_data) > 0:
            logger.info(f"Processing chat with CSV data ({len(csv_data)} records)")
            
            # Create a temporary directory if it doesn't exist
            temp_dir = os.path.join(os.getcwd(), 'temp_files')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save CSV to a temporary file
            temp_csv = os.path.join(temp_dir, 'query_data.csv')
            df = pd.DataFrame(csv_data)
            df.to_csv(temp_csv, index=False)
            logger.info(f"Saved CSV data to {temp_csv}")
            
            # Use the CLI-based approach
            response_text = ai_service.ask_question_with_csv(user_message, temp_csv)
            logger.info("Got response from CLI-based approach")
        else:
            # Regular API call for standard questions
            logger.info("No CSV data provided, using standard API call")
            response_text = ai_service.ask_question(user_message)
        
        # Return the response
        return jsonify({
            'response': response_text,
            'csvData': csv_data  # Return the CSV data back
        })
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}"})

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file part'})
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
            
        if file and file.filename.endswith('.csv'):
            # Read the CSV data
            df = pd.read_csv(file)
            
            # Convert to list of dictionaries
            csv_data = df.to_dict('records')
            
            # Log for debugging
            logger.info(f"CSV loaded successfully with {len(csv_data)} records")
            logger.info(f"Sample data: {csv_data[:2] if len(csv_data) > 2 else csv_data}")
            
            # Store the original filename
            filename = secure_filename(file.filename)
            
            # Save a copy of the file for future reference
            temp_dir = os.path.join(os.getcwd(), 'temp_files')
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, filename)
            df.to_csv(temp_file_path, index=False)
            logger.info(f"Saved CSV to {temp_file_path}")
            
            # Return success response with data
            return jsonify({
                'success': True,
                'data': csv_data,
                'filename': filename,
                'message': f"CSV loaded successfully with {len(csv_data)} records"
            })
        else:
            return jsonify({'success': False, 'error': 'File must be a CSV'})
            
    except Exception as e:
        logger.error(f"Error processing CSV upload: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download-csv', methods=['POST'])
def download_csv():
    try:
        # Get data from request
        data = request.json
        csv_data = data.get('data', [])
        filename = data.get('filename', 'jira_tasks.csv')
        
        # Convert to DataFrame
        df = pd.DataFrame(csv_data)
        
        # Create a temporary file
        temp_dir = os.path.join(os.getcwd(), 'temp_files')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, 'download_' + filename)
        df.to_csv(temp_path, index=False)
        
        # Return the file
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
            
    except Exception as e:
        logger.error(f"Error processing CSV download: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download-model', methods=['POST'])
def download_model():
    data = request.json
    model_name = data.get('model', '')
    
    if not model_name:
        return jsonify({'success': False, 'error': 'No model specified'})
    
    try:
        # Use Ollama CLI to pull the model
        logger.info(f"Downloading model: {model_name}")
        result = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully downloaded model: {model_name}")
            return jsonify({'success': True})
        else:
            error_msg = result.stderr or "Unknown error pulling model"
            logger.error(f"Failed to download model: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5002)