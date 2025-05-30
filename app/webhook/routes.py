from flask import Blueprint, jsonify, request, render_template, render_template_string
from ..extensions import mongo
from datetime import datetime
from dateutil.parser import parse as parse_datetime


webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

@webhook.route('/receiver', methods=["POST"])
def receiver():
    data = request.json
    event = request.headers.get("X-GitHub-Event")
    request_id = request.headers.get('X-GitHub-Delivery')
    response_msg = ""

    if event == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        timestamp = data["head_commit"]["timestamp"]
        commit_msg = data["head_commit"]["message"]

        # Detect if it's a merge commit from a pull request
        if "merge pull request" in commit_msg.lower():
            parts = commit_msg.split("from ")
            if len(parts) > 1:
                raw_from_branch = parts[1].strip()
                # Clean up branch name (remove newline, extract last part)
                first_line = raw_from_branch.split("\n")[0]
                from_branch = first_line.split("/")[-1]
            else:
                from_branch = "unknown"

        else:
            response_msg = f"{author} pushed to {to_branch} on {timestamp}"

            mongo.db.events.insert_one({
                "request_id" : request_id,
                "action": "push",
                "author": author,
                "from_branch": None,
                "to_branch": to_branch,
                "timestamp": timestamp
            })

    elif event == "pull_request":
        action = data.get("action")
        pr = data["pull_request"]
        author = pr["user"]["login"]
        from_branch = pr["head"]["ref"]
        to_branch = pr["base"]["ref"]

        if action == "opened":
            timestamp = pr["created_at"]
            response_msg = f"{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}"

            mongo.db.events.insert_one({
                "request_id" : request_id,
                "action": "pull_request",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            })
        
        elif action == "closed" and pr.get("merged"):

            timestamp = pr["merged_at"]
            response_msg = f"{author} merged branch {from_branch} to {to_branch} on {timestamp}"

            mongo.db.events.insert_one({
                "request_id" : request_id,
                "action": "merge",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            })

    else:
        response_msg = f"Ignored event type: {event}"

    print(response_msg)
    return jsonify({"status": "success", "message": response_msg}), 200