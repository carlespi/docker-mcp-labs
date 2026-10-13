from flask import Flask

app = Flask(__name__)

@app.route("/welcome")
def home():
    return "Hello from Python running inside Docker!\n"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
