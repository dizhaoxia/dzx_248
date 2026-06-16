import os
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['UPLOAD_FOLDER'] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'uploads'
    )
    app.config['INDEX_DIR'] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'index'
    )
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['INDEX_DIR'], exist_ok=True)

    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
