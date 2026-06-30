"""
Entry point for the Flask backend.
"""
from flask import Flask
from flask_cors import CORS
from routes import process_bp
from routes_schema import schema_bp

def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

    CORS(app, resources={r"/*": {"origins": "*"}})

    app.register_blueprint(process_bp)
    app.register_blueprint(schema_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
