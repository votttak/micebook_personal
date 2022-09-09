
###
# Backend for Viruses (button on the top of the main page and some of the others).
# Procedures for navigating the virus table, updating, adding, deleting a virus
###

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from flask import Flask, json, jsonify
from flaskr.auth import login_required
from . import db, Mice, Procedures, Steps, Entries, Viruses, Users, Experiment_actions
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
bp = Blueprint('virus', __name__)

## geting to the list of viruses ## 
@bp.route('/virus_index', methods=('GET', 'POST'))
@login_required
def index():
    for item in request.form:
        print(item)
        print("--------")
    if request.method=='POST':
        if 'virus_index_name' in request.form:
            virus_name = request.form['virus_index_name']
            virus_list = Viruses.query.filter(Viruses.name==virus_name).order_by(asc(Viruses.id)).all()
    else:
        virus_list = Viruses.query.order_by(asc(Viruses.id)).all() 
    return render_template('virus/index.html', virus_list=virus_list)


## get the virus from the database according "id" ##
def get_virus(id):
    virus = Viruses.query.filter(Viruses.id==id).first()
    if virus is None:
        abort(404, "Mouse id {0} doesn't exist.".format(id))
    return virus

## changing existing virus ##
@bp.route('/<int:virus_id>/virus_update', methods=('GET', 'POST'))
@login_required
def virus_update(virus_id):
    virus = get_virus(virus_id)
    if request.method == 'POST':
        name = request.form['name']
        construct = request.form['construct']
        container = request.form['container']
        error = None
        already_exist = Viruses.query.filter(Viruses.id!=virus_id, Viruses.name==name).first()
        if already_exist:
            error = 'Virus name already exists'
        elif not construct:
            error = 'Construct is required'
        if not container:
            error = 'Container is required.'

        if error is not None:
            flash(error)
        else:
            inputs = request.form.to_dict(flat=True)
            db.session.query(Viruses).filter(Viruses.id == virus_id).update(inputs)
            db.session.commit()
            return redirect(url_for('virus.index'))
    return render_template('virus/virus_update.html', virus=virus)

## deleting virus ## 
@bp.route('/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
    virus = get_virus(id)
    print("DDDDDDDDDDDDDDDDD")
    print(virus)
    print("DDDDDDDDDDDDDDDDD")
    db.session.delete(virus)
    db.session.commit()
    return redirect(url_for('virus.index'))

## add new virus ##
@bp.route('/new_virus', methods=('GET', 'POST'))
@login_required
def add_virus():
    print("in virus.py: add_virus")
    if request.method == 'POST':
        name = request.form['name']
        construct = request.form['construct']
        container = request.form['container']

        error = None
        already_exist = Viruses.query.filter(Viruses.name==name).first()
        if already_exist:
            error = 'Virus name already exists'
        elif not construct:
            error = 'Construct is required'
        if not container:
            error = 'Container is required.'

        if error is not None:
            flash(error)
        else:
            inputs = request.form.to_dict(flat=True)
            print(inputs)
            virus = Viruses(**inputs)
            db.session.add(virus)
            db.session.commit()
            return redirect(url_for('virus.index'))

    return render_template('virus/new_virus.html')