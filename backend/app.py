from flask import Flask, jsonify
from flask_cors import CORS
from config import config

# 导入蓝图
from routes.agent_routes import agent_bp
from routes.chat_routes import chat_bp
from routes.design_data_routes import design_data_bp
from routes.spatial_routes import spatial_bp
from routes.project_routes import project_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    CORS(app)  # 允许跨域，方便前端Next.js访问
    
    # 注册路由蓝图
    app.register_blueprint(agent_bp, url_prefix='/agents')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(design_data_bp, url_prefix='/design')
    app.register_blueprint(spatial_bp, url_prefix='/spatial')
    app.register_blueprint(project_bp, url_prefix='/project')
    
    @app.route('/')
    def index():
        
        return jsonify({"message": "Hello from Flask Backend!"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
