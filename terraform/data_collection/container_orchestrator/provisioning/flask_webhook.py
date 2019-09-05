from flask import Flask, jsonify, request
import hashlib
import hmac
import json

app = Flask(__name__)


def verify_signature(data, signature):
    with open("/var/www/github.secret", "r") as f_secret:
        github_secret = f_secret.readlines()[0].strip()
    mac = hmac.new(github_secret.encode(), msg=data, digestmod=hashlib.sha1)
    return hmac.compare_digest("sha1=" + mac.hexdigest(), signature)


@app.route("/")
def default():
    return "Flask server for github webhooks"


@app.route("/github", methods=["POST"])
def github_webhook():
    print("Processing webhook request...")
    request.get_data()
    signature = request.headers.get("X-Hub-Signature")
    data = request.data
    if verify_signature(data, signature):
        print("Verified GitHub signature: {}".format(signature))
        if request.is_json:
            print("Processing application/json")
            payload_dict = request.json
        else:
            print("Processing application/x-www-form-urlencoded")
            request_dict = request.form.to_dict()
            payload_dict = json.loads(request_dict["payload"])
        action = payload_dict.get("action", None)
        try:
            merged = payload_dict["pull_request"]["merged"]
        except KeyError:
            merged = False
        print("Action was {}, merged was {}".format(action, merged))
        if action == "closed" and merged:
            with open("/var/www/latest_commit_hash", "w") as f_output:
                f_output.write(payload_dict["pull_request"]['head']['sha'])
            print("=> called the code updater")
            return jsonify({"msg": "called code updater"})
        print("=> no action needed as this is not a merged pull request")
        return jsonify({"msg": "no action needed as this is not a merged pull request"})
    else:
        print("Failed to verify GitHub signature: {}".format(signature))
        return jsonify({"msg": "invalid hash"})
    print("Unknown issue")
    return jsonify({"msg": "unknown issue"})


if __name__ == "__main__":
    app.run()
