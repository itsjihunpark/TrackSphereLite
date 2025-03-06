import os
from flask import Flask
from flask_restx import Api, Resource, fields
from flask_socketio import SocketIO

socket = SocketIO()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'SECRET_KEY',
        DATABASE=os.path.join(app.instance_path, 'piTrackSphere.sqlite')
    )
    
    from .model.db import DataAccess
    db_access = DataAccess()
    db_access.init_app(app)

    from .blueprints import auth
    app.register_blueprint(auth.bp) 

    from .blueprints import options
    app.register_blueprint(options.bp)
    
    
    from .blueprints import monitor
    app.register_blueprint(monitor.bp)

    from .blueprints import review
    app.register_blueprint(review.bp)

    api_main = Api(version="1.0", title="Api", doc='/api/doc')
    api_main.init_app(app)

    from .blueprints.api.metric_calculation import api
    api_main.add_namespace(api, path="/metric_calculation")
    
    from .blueprints.api.camera_controls import api
    api_main.add_namespace(api, path="/camera_controls")
    
    app.add_url_rule('/', endpoint='index')

    socket.init_app(app)


    return app