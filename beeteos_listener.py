import queue

from flask import Flask, request

app = Flask(__name__)
account_id_queue = queue.Queue()


@app.route("/set_account_id", methods=["POST"])
def set_account_id():
    data = request.get_json()
    if "account_id" in data:
        account_id_queue.put(data["account_id"])
        return "Account ID received", 200
    return "Invalid request", 400


def run_listener():
    app.run(port=5000)
