import os
from flask import Flask
from routes import register_blueprints

def create_app():
    app = Flask(__name__)
    register_blueprints(app)
    return app

app = create_app()

@app.route("/")
def index():
    return "Webhook service is running!"

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 3000))  # Render/Heroku sets PORT
#     app.run(host="0.0.0.0", port=port, debug=True)
