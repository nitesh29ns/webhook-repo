from flask import Flask
from .extensions import mongo

from app.webhook.routes import webhook


# Creating our flask app
def create_app():

    app = Flask(__name__)

    # configure mongodb url
    app.config["MONGO_URI"] = "mongodb+srv://nitesh8527:Nitesh8527@cluster0.bxxtr.mongodb.net/github-webhook?retryWrites=true&w=majority&appName=Cluster0"
    
    # initialize PyMongo
    mongo.init_app(app) 
    
    # registering all the blueprints
    app.register_blueprint(webhook)
    
    return app