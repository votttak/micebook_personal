##
# v_11 (22.01.2022)
##

import os

from flask import Flask, json, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from urllib.parse import quote_plus as urlquote
from flask_bootstrap import Bootstrap
#from .momentjs import momentjs
from flask_moment import Moment
from sys import platform

db = SQLAlchemy()
moment = Moment()
from .tables import *


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = '199701'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    #app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://vadim:qQ1234567@localhost:5432/myinner_micebook_db"
    
    if platform == "win32":
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://vadim:qQ1234567@localhost:5432/myinner_micebook_db"
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://miceuser:vyo8eixOr73XjzX3CdkUWSnnVputKFwZr27Rz9x9F7obXvboom1c8cpc1zvB5btZ@localhost/micebook"
       
    moment.init_app(app)
    db.init_app(app)
    with app.app_context():
        #db.drop_all()  ## CAREFULL!!!! Uncomment to delete all tables and their content
        db.create_all()

    
    migrate = Migrate(app, db)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    

    from . import auth
    app.register_blueprint(auth.bp)

    from . import mouse
    app.register_blueprint(mouse.bp)
    app.add_url_rule('/', endpoint='index')

    from . import experiments
    app.register_blueprint(experiments.bp)
 
    from . import virus
    app.register_blueprint(virus.bp) 
    
    from . import coordinates
    app.register_blueprint(coordinates.bp) 

    return app



# if __name__ == "__main__":


#     Load_Mice('C:/Users/maxim/Documents/ETH/Micebook/configurableAnimal.csv', db, Mice)

#db.create_all(app=create_app)