from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#database setup
db = SQLAlchemy()

# Get database configuration from environment variables
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'Fist-1211204126.')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'FYP')

#database URI
DB_URI = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

def create_app():
    app = Flask(__name__,template_folder='templates', static_folder='static')

    # Configure the Flask app with the database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    #bind the database to the app
    db.init_app(app)

    #reflect the database schema
    with app.app_context():
        # Call the reflect() method on the extension. It will reflect all the tables for each bind key. 
        # Each metadata's tables attribute will contain the detected table objects.
        db.reflect()

        # Import and register routes
        from routes import page_routes, api_routes
        page_routes(app)
        api_routes(app)

    return app


#syntax
# with app.app_context():
#     db.reflect()

# # From the default bind key
# class Book(db.Model):
#     __table__ = db.metadata.tables["book"]