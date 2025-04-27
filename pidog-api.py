import os
import sys
import json
import subprocess
from flask import Flask, jsonify

# Load configuration from JSON file
CONFIG_PATH = os.environ.get('CONFIG_PATH', 'pidog-api-config.json')

def load_config(path):
    if not os.path.isfile(path):
        print(f"Config file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}", file=sys.stderr)
        sys.exit(1)

config = load_config(CONFIG_PATH)

# Directory containing allowed Python scripts
SCRIPTS_DIR = config.get('scripts_dir')
if not SCRIPTS_DIR:
    print("'scripts_dir' not defined in config.", file=sys.stderr)
    sys.exit(1)

# Map of allowed keywords to script filenames
SCRIPT_MAP = config.get('script_map', {})
if not isinstance(SCRIPT_MAP, dict) or not SCRIPT_MAP:
    print("'script_map' not defined or invalid in config.", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)

@app.route("/run-script/<key>", methods=["GET"])
def run_script(key):
    # Only allow execution of mapped scripts
    if key not in SCRIPT_MAP:
        return jsonify({"error": "Script not allowed."}), 403

    filename = SCRIPT_MAP[key]
    script_path = os.path.join(SCRIPTS_DIR, filename)

    # Ensure the resolved filename matches exactly to prevent traversal
    if os.path.basename(script_path) != filename:
        return jsonify({"error": "Invalid script configuration."}), 400

    if not os.path.isfile(script_path):
        return jsonify({"error": f"Script '{filename}' not found."}), 404

    try:
        # Execute the script and capture output
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=config.get('timeout', 30)
        )
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script execution timed out."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    host = config.get('host', '0.0.0.0')
    port = config.get('port', 5000)
    app.run(host=host, port=port)
