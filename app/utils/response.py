from flask import jsonify

def success_response(data=None, message="Success", code=200, status="success"):
    response = {
        "status": status,
        "message": message,
        "data": data
    }
    return jsonify(response), code

def error_response(message="An error occurred", code=400, data=None):
    return jsonify({
        "status": "error",
        "message": message,
        "data": data
    }), code
