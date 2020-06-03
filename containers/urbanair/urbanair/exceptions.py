from flask import jsonify

# Return validation errors as JSO


def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


def error_handler(app):
    app.register_error_handler(422, handle_error)
    app.register_error_handler(400, handle_error)
