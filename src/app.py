from flask import Flask, render_template_string, request
import requests
import json
from requests_aws4auth import AWS4Auth
import boto3

app = Flask(__name__)

API_URL = "https://0bb62kmym8.execute-api.ap-south-1.amazonaws.com/dev_ravi"
REGION = "ap-south-1"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>EC2 Instance Control</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .btn-group-actions .btn { min-width: 150px; }
        .ssh-code { color: #c2185b; }
        .muted { color: #6c757d; font-size: 0.9rem; }
    </style>
</head>
<body class="bg-light">
    <div class="container my-4">
        <div class="card shadow-sm">
            <div class="card-body">
                <h2 class="card-title text-center mb-4">EC2 Instance Control</h2>

                <form method="POST" action="/ec2">
                    <div class="d-flex justify-content-center btn-group-actions gap-2 mb-3 flex-wrap">
                        <button type="submit" name="action" value="create" class="btn btn-primary">Create Instance</button>
                        <button type="submit" name="action" value="start" class="btn btn-success">Start Instance</button>
                        <button type="submit" name="action" value="stop" class="btn btn-danger">Stop Instance</button>
                        <button type="submit" name="action" value="terminate" class="btn btn-warning">Terminate Instance</button>
                    </div>

                    <div class="mb-3">
                        <label for="instance_id" class="form-label">Select EC2 Instance</label>
                        <select id="instance_id" name="instance_id" class="form-select">
                            <option value="" disabled selected>Select an instance</option>
                            {% for inst in instances %}
                                <option value="{{ inst['InstanceId'] }}">
                                    {{ inst['InstanceId'] }} - {{ inst['State'] }} - {{ inst['PublicIpAddress'] or 'No Public IP' }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                </form>

                {% if message %}
                    {% set lower = message|lower %}
                    <div class="alert
                        {{
                            'alert-success' if ('created' in lower or 'success' in lower or 'started' in lower or 'stopped' in lower or 'terminated' in lower)
                            else ('alert-warning' if 'please' in lower
                            else ('alert-danger' if 'error' in lower
                            else 'alert-info'))
                        }} mt-3">
                        <div class="d-flex align-items-center">
                            {% if 'created' in lower %}
                                <span class="me-2">✅</span><strong>Instance created successfully!</strong>
                            {% elif 'started' in lower %}
                                <span class="me-2">✅</span><strong>Instance started successfully!</strong>
                            {% elif 'stopped' in lower %}
                                <span class="me-2">✅</span><strong>Instance stopped successfully!</strong>
                            {% elif 'terminated' in lower %}
                                <span class="me-2">✅</span><strong>Instance terminated successfully!</strong>
                            {% elif 'please' in lower %}
                                <span class="me-2">❌</span><strong>{{ message|safe }}</strong>
                            {% elif 'error' in lower %}
                                <span class="me-2">❌</span><strong>{{ message|safe }}</strong>
                            {% else %}
                                <strong>{{ message|safe }}</strong>
                            {% endif %}
                        </div>
                    </div>
                {% endif %}

                {% if details or (message and 'created' in message|lower) %}
                    <div class="alert alert-success mt-3">
                        
                        <div><strong>SSH Command:</strong></div>
                        <div class="ssh-code mt-1">
                            {{ details.ssh_command if details and details.ssh_command else '(ssh command not provided)' }}
                        </div>
                        <div class="muted mt-2">
                            {% set parts = [] %}
                            {% if details and details.instance_id %}{% set _ = parts.append('Instance ID: ' ~ details.instance_id) %}{% endif %}
                            {% if details and details.key_name %}{% set _ = parts.append('Key: ' ~ details.key_name) %}{% endif %}
                            {% if details and details.public_ip %}{% set _ = parts.append('Public IP: ' ~ details.public_ip) %}{% endif %}
                            {% if details and details.username %}{% set _ = parts.append('Username: ' ~ details.username) %}{% endif %}
                            {{ parts|join(' • ') }}
                        </div>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

ec2 = boto3.client('ec2', region_name=REGION)

def fetch_all_instances():
    instances = []
    try:
        paginator = ec2.get_paginator('describe_instances')
        for page in paginator.paginate():
            for reservation in page.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        'InstanceId': instance.get('InstanceId'),
                        'State': instance.get('State', {}).get('Name'),
                        'PublicIpAddress': instance.get('PublicIpAddress')
                    })
    except Exception as e:
        print(f"Error fetching instances: {e}")
    return instances

def call_api(payload):
    session = boto3.Session()
    credentials = session.get_credentials()
    if not credentials:
        raise RuntimeError("No AWS credentials available for signing the API request.")
    headers = {
        "Content-Type": "application/json"
    }
    awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    "execute-api",
    session_token=credentials.token
)

    resp = requests.post(API_URL, json=payload, auth=awsauth,headers=headers)

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Non-JSON response from API: {resp.text}")

    if isinstance(data, dict) and "statusCode" in data and "body" in data:
        try:
            body = json.loads(data["body"])
        except Exception:
            body = data["body"]
        return data.get("statusCode"), body
    else:
        return resp.status_code, data
    
@app.route("/ec2", methods=["GET", "POST"])
def ec2_control():
    message = None
    result = None
    details = None  # structured fields for UI

    if request.method == "POST":
        action = request.form.get("action")
        instance_id = request.form.get("instance_id")

        if action == "create":
            payload = {"action": "create"}
        else:
            if not instance_id:
                message = "Please select an instance."
                instances = fetch_all_instances()
                return render_template_string(HTML, message=message, result=result, instances=instances, details=details)
            payload = {"action": action, "instance_id": instance_id}

        try:
            status_code, body = call_api(payload)

            # Always try to extract a message if present (case-insensitive)
            body_dict = body if isinstance(body, dict) else None
            if body_dict:
                message = (
                    body_dict.get("message")
                    or body_dict.get("Message")
                    or body_dict.get("msg")
                )

                # Prefer body["data"] if it’s a dict; otherwise use the body itself
                source = body_dict.get("data") if isinstance(body_dict.get("data"), dict) else body_dict

                # Extract known fields for UI and normalize keys
                key_map = {
                    "ssh_command": "ssh_command",
                    "public_ip": "public_ip",
                    "username": "username",
                    "instance_id": "instance_id",
                    "key_name": "key_name",
                    # common alternative keys
                    "PublicIpAddress": "public_ip",
                    "InstanceId": "instance_id",
                    "KeyName": "key_name",
                }
                picked = {}
                for k, norm in key_map.items():
                    v = source.get(k) if isinstance(source, dict) else None
                    if v:
                        picked[norm] = v
                if picked:
                    details = picked

                # Synthesize a friendly message if API didn't send one but call was OK
                if not message and 200 <= (status_code or 0) < 300:
                    verb_map = {"create": "created", "start": "started", "stop": "stopped", "terminate": "terminated"}
                    suffix = verb_map.get((action or "").lower(), "completed")
                    message = f"Instance {suffix} successfully!"

                # Keep raw extra for debugging parity (not shown in UI)
                extra = body_dict.get("data")
                if extra:
                    result = json.dumps(extra, indent=2)

            else:
                # Non-dict body; keep as string (not displayed, but preserved)
                result = json.dumps(body, indent=2) if isinstance(body, (dict, list)) else str(body)
                if 200 <= (status_code or 0) < 300 and not message:
                    # Generic fallback success
                    verb_map = {"create": "created", "start": "started", "stop": "stopped", "terminate": "terminated"}
                    suffix = verb_map.get((action or "").lower(), "completed")
                    message = f"Instance {suffix} successfully!"

        except Exception as e:
            message = f"Error calling API: {str(e)}"

    instances = fetch_all_instances()
    return render_template_string(HTML, message=message, result=result, instances=instances, details=details)
if __name__ == "__main__":
    app.run(debug=True)
