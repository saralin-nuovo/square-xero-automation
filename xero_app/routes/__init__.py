from flask import Blueprint
from .auth_routes import auth_bp
from .invoice_routes import invoice_bp
from .contact_routes import contact_bp
from .square_routes import square_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(square_bp)   
