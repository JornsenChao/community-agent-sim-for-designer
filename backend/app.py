from flask import Flask
from flask_cors import CORS
from config import config
from models import db, GeoFeature
import sqlalchemy
import os

# 导入蓝图
from routes.agent_routes import agent_bp
from routes.chat_routes import chat_bp
from routes.design_data_routes import design_data_bp
from routes.spatial_routes import spatial_bp
from routes.project_routes import project_bp
from routes.geo_routes import geo_bp

def create_app():
    app = Flask(__name__)
    # app.config.from_object(config)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    CORS(app)
    db.init_app(app)
    
    
    with app.app_context():
        # 如果表不存在，则创建
        db.create_all()
    
    # 注册路由蓝图
    app.register_blueprint(agent_bp, url_prefix='/agents')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(design_data_bp, url_prefix='/design')
    app.register_blueprint(spatial_bp, url_prefix='/spatial')
    app.register_blueprint(project_bp, url_prefix='/project')
    app.register_blueprint(geo_bp, url_prefix="/geo")
    
    @app.route('/')
    def index():
        return {"message": "Hello from Flask + PostGIS!"}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
