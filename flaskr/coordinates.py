from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from flask import Flask, json, jsonify
from flaskr.auth import login_required
from . import db, Mice, Procedures, Steps, Entries, Viruses, Users, Experiment_actions, Coordinates
from sqlalchemy import desc, asc
from sqlalchemy import engine
from .experiment_trees import next_procedure
from .external_communications import Load_Mice, Load_Viruses
from sqlalchemy import func
from sqlalchemy.sql import text
from datetime import datetime
from .external_communications import interprete, irats_fetch
from.experiments import Functions, Steps_names
from pathlib import Path
import os
from sys import platform
from sqlalchemy import and_, or_

#from .experiments
bp = Blueprint('coordinates', __name__)

@bp.route('/coordinates_index', methods=('GET', 'POST'))
@login_required
def index():
    if request.method=='POST':
        # ??? virus_index_name 
        print("coordinates.py: index(): request.method=='POST'")
        print("coordinates.py: index(): request.method=='POST': request.form")
        print(request.form)
        if 'coordinates_index_name' in request.form:

            print("coordinates.py: if 'coordinates_index_name' in request.form: TRUE")

            coordinates_name = request.form['coordinates_index_name']
            print("'" + coordinates_name + "'")
            coordinates_list = Coordinates.query.filter(Coordinates.name==coordinates_name).order_by(asc(Coordinates.id)).all()
            coordinates_list = Coordinates.query.filter(Coordinates.name=="prelimbic cortex").all()
            coordinates_list = Coordinates.query.order_by(asc(Coordinates.id)).all() 
            print("----------")
            print(coordinates_list)
    else:
        coordinates_list = Coordinates.query.order_by(asc(Coordinates.id)).all() 

    # ??? coordinates_list as argument in render_template ??? --> скорее всего это для {% for coordinates in coordinates_list %}
    return render_template('coordinates/index.html', coordinates_list=coordinates_list)


def get_coordinates(id):
    coordiantes = Coordinates.query.filter(Coordinates.id==id).first()

    if coordiantes is None:
        abort(404, "Coordinates id {0} doesn't exist.".format(id))

    return coordiantes


@bp.route('/<int:coordinates_id>/coordinates_update', methods=('GET', 'POST'))
@login_required
def coordinates_update(coordinates_id):
    coordinates = get_coordinates(coordinates_id)
    if request.method == 'POST':

        name = request.form['name']
        error = None
        already_exist = Coordinates.query.filter(Coordinates.id!=coordinates_id, Coordinates.name==name).first()
        
        if already_exist:
            error = 'Coordinates name already exists'
     
        if error is not None:
            flash(error)
        else:
            inputs = request.form.to_dict(flat=True)
            db.session.query(Coordinates).filter(Coordinates.id == coordinates_id).update(inputs)
            db.session.commit()
            return redirect(url_for('coordinates.index'))

    return render_template('coordinates/coordinates_update.html', coordinates=coordinates)


@bp.route('/<int:id>/delete_coordinates', methods=('GET', 'POST'))
@login_required
def delete(id):
    coordinates = get_coordinates(id)
    db.session.delete(coordinates)
    db.session.commit()
    return redirect(url_for('coordinates.index'))


@bp.route('/new_coordinates', methods=('GET', 'POST'))
@login_required
def add_coordinates():
    if request.method == 'POST':
        name = request.form['name']
        
        error = None
        already_exist = Coordinates.query.filter(Coordinates.name==name).first()
        if already_exist:
            error = 'Coordinates name already exists'
       

        if error is not None:
            flash(error)
        else:
            inputs = request.form.to_dict(flat=True)
            coordinates = Coordinates(**inputs)
            db.session.add(coordinates)
            db.session.commit()
            return redirect(url_for('coordinates.index'))

    return render_template('coordinates/new_coordinates.html')