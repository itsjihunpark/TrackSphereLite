import os
from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'SECRET_KEY',
        DATABASE=os.path.join(app.instance_path, 'piTrackSphere.sqlite')
    )

    from .model.db import DataAccess
    db_access = DataAccess()
    db_access.init_app(app)



    from .controller import auth
    app.register_blueprint(auth.bp) 

    from .controller import options
    app.register_blueprint(options.bp)
    
    from .controller import monitor
    app.register_blueprint(monitor.bp)
    
    from .controller import review
    app.register_blueprint(review.bp)


    from .controller.rest_api import rest_api
    rest_api.init_app(app)

    app.add_url_rule('/', endpoint='index')

    return app