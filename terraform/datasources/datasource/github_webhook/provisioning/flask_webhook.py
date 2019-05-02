from flask import Flask, jsonify, request
import hashlib
import hmac

app = Flask(__name__)

def verify_signature(data, signature):
    with open("/var/www/github.secret", "r") as f_secret:
        github_secret = f_secret.readlines()[0].strip()
    mac = hmac.new(github_secret.encode(), msg=data, digestmod=hashlib.sha1)
    return hmac.compare_digest('sha1=' + mac.hexdigest(), signature)

@app.route("/")
def default():
    return "Flask server for github webhooks"

@app.route("/github", methods=['POST'])
def github_webhook():
    print("Processing webhook request...")
    request.get_data()
    signature = request.headers.get('X-Hub-Signature')
    data = request.data
    if verify_signature(data, signature):
        print("Verified GitHub signature: {}".format(signature))
    with open("/var/www/update_needed", "w") as f_output:
        f_output.write("yes")
        return jsonify({'msg': 'Ok'})
    print("Failed to verify GitHub signature: {}".format(signature))
    return jsonify({'msg': 'invalid hash'})

if __name__ == "__main__":
    app.run()