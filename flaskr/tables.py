

###
# Tables defined using SQLalchemy logic.
# Those are generated upon launch of the server. 
# db (database object) imported from __init__.py 
# If a database with a data already exists, the tables here and in the DB have to align, otherwise update the database.  
# Remark: Follow Migration Update procedure when updating DB, in the terminal running the app
#         - flask db migrate -m "database update name"
#         - flask db upgrade
###

import os
from . import db
from datetime import datetime

class Users(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.Text())
    full_name = db.Column(db.String())
    admin_rights = db.Column(db.Boolean())
    email = db.Column(db.String())

    def __repr__(self):
        return f"<User {self.username}>"

class Mice(db.Model):
    __tablename__ = 'mice'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    irats_id = db.Column(db.String())
    system_id = db.Column(db.String())
    cage = db.Column(db.String())
    licence = db.Column(db.Text())
    strain = db.Column(db.String())
    genotype = db.Column(db.String())
    gender = db.Column(db.String())
    birthdate = db.Column(db.String()) 
    status = db.Column(db.String())
    experiment = db.Column(db.String())
    investigator = db.Column(db.String())
    severity = db.Column(db.String())
    euthanized = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return f"<Mouse {self.id}>"

class Procedures(db.Model):
    __tablename__='procedures'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    mouse_id = db.Column(db.Integer())
    finished = db.Column(db.Boolean()) #In Progress, Done

    def __init__(self, name, mouse_id, finished=False):
        self.name = name
        self.mouse_id = mouse_id
        self.finished = finished

    def __repr__(self):
        return f"<Procedure {self.id}>"

class Steps(db.Model):
    __tablename__='steps'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    mouse_id = db.Column(db.Integer())
    procedure_id = db.Column(db.Integer())
    user_id = db.Column(db.Integer())
    # time = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    comment = db.Column(db.Text())

    def __init__(self, name, mouse_id, procedure_id, user_id, comment=None):
        self.name = name
        self.mouse_id = mouse_id
        self.procedure_id = procedure_id
        self.user_id = user_id
        self.comment = comment

    def __repr__(self):
        return f"<Step {self.id}>"

class Entries(db.Model):
    __tablename__='entries'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    step_id = db.Column(db.Integer())
    # user_id = db.Column(db.Integer())
    entry_format = db.Column(db.Text, nullable=False) 
    content = db.Column(db.Text())
    next_entry_in = db.Column(db.Interval())
    reference_weight = db.Column(db.Boolean())

    def __repr__(self):
        return f"<Entry {self.id}>"

class Viruses(db.Model):
    __tablename__='viruses'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    # print("tables.py in Viruses")
    # print("db.String()")
    # print(db.String())
    # print("db.Text")
    # print(db.Text)
    # print("db.Integer")
    # print(db.Integer)
    # print("db.Float")
    # print(db.Float)
    container = db.Column(db.String())
    producer = db.Column(db.String())
    promoter = db.Column(db.String())
    expressing_protein = db.Column(db.String())
    dependency = db.Column(db.String())
    serotype = db.Column(db.String())
    fluorophob = db.Column(db.String())
    titer = db.Column(db.String())
    dilution = db.Column(db.String())
    construct = db.Column(db.String())

    def __repr__(self):
        return f"<Virus {self.id}>"


class Coordinates(db.Model):
    __tablename__ = 'coordinates'
    # ???
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    region_name_abbreviated = db.Column(db.String())
    AP = db.Column(db.Float)
    ML = db.Column(db.Float)
    DV = db.Column(db.Float)
    researcher = db.Column(db.String())

    def __repr__(self):
        return f"<Coordinates {self.id}>"


class Experiments(db.Model):
    __tablename__='experiments'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer())
    project_id = db.Column(db.Integer())
    
    def __repr__(self):
        return f"<Experiment {self.id}>"

class Experiment_actions(db.Model):
    __tablename__='experiment_actions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    experiment_id = db.Column(db.Integer())
    index = db.Column(db.Integer)
    final = db.Column(db.Boolean())
    
    def __repr__(self):
        return f"<Experiment_action {self.id}>"

class Licences(db.Model):
    __tablename__='licences'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(), nullable=False)
    name = db.Column(db.Text, nullable=False)
    holder = db.Column(db.String())
    valid_through = db.Column(db.String())
    
    def __repr__(self):
        return f"<Licence {self.id}>"

class Projects(db.Model):
    __tablename__='projects'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.Text, nullable=False)
    licence_id = db.Column(db.Integer())
    user_id = db.Column(db.Integer())
    
    def __repr__(self):
        return f"<Project {self.id}>"