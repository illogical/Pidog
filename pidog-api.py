from flask import Flask, jsonify
import os
import subprocess

app = Flask(__name__)

# Directory containing allowed Python scripts
SCRIPTS_DIR = "/path/to/scripts"

@app.route("/run-script/<filename>", methods=["GET"])
def run_script(filename):
    # Prevent directory traversal attacks
    if os.path.basename(filename) != filename:
        return jsonify({"error": "Invalid filename."}), 400

    script_path = os.path.join(SCRIPTS_DIR, filename)
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
