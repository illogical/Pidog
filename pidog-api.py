from flask import Flask, jsonify
import os
import subprocess

app = Flask(__name__)

# Directory containing allowed Python scripts
SCRIPTS_DIR = "/path/to/scripts"

# Map of allowed keywords to script filenames
SCRIPT_MAP = {
    "backup": "backup_script.py",
    "update": "update_script.py"
}

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
            timeout=30
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
    app.run(host="0.0.0.0", port=5000)
