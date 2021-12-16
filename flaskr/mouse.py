from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from flaskr.tables import Coordinates
from werkzeug.exceptions import abort
from flask import Flask, json, jsonify
from flaskr.auth import login_required
from . import db, Mice, Procedures, Steps, Entries, Viruses, Users, Experiment_actions
from sqlalchemy import desc, asc
from sqlalchemy import engine
from .experiment_trees import next_procedure
from .external_communications import Load_Mice
from sqlalchemy import func
from sqlalchemy.sql import text
from datetime import datetime
from .external_communications import interprete, irats_fetch, download_licences, download_user_projects
from.experiments import Functions, Steps_names
from pathlib import Path
import os
from sys import platform
from sqlalchemy import and_, or_

#from .experiments
bp = Blueprint('mouse', __name__)

def time_display(delta):
    days = delta.days
    if days >0:
        return 'in '+str(days)+' days', "color: green"
    elif days==0:
        return 'today', "color: orange"
    else:
        return str(abs(days))+' days ago', "color: red"

@bp.route('/', methods=('GET', 'POST'))
@login_required
def index(show_all=False):
    if platform=="win32":
        animal_csv_filename = os.path.join(Path().resolve().parents[0], "configurableAnimal.csv")
    else:
        animal_csv_filename = "/var/www/mfabre/webapp/configurableAnimal.csv"

    try:
        Load_Mice(animal_csv_filename, db, Mice)
    except:
        flash('ConfigureAnimal.csv file is erroneous. Please reload mice from irats and retry or ask the person in charge for manual check')

    todo_mice_sql = """SELECT *, TO_TIMESTAMP(step.content, 'YYYY-MM-DD"T"HH24:MI')+ step.next_entry_in AS next_operation FROM mice JOIN (SELECT DISTINCT ON (mouse_id) *FROM ( SELECT *FROM steps JOIN      (SELECT  *FROM      entries WHERE  id in (SELECT MAX(id) FROM entries WHERE next_entry_in IS NOT NULL GROUP BY step_id)) e ON (e.step_id = steps.id) ) AS lastentries ORDER BY mouse_id, step_id DESC) step ON (mice.id=step.mouse_id) WHERE mice.id not in (SELECT mouse_id FROM steps WHERE name = 'Euthanasia') """
    order_by_sql =    """ ORDER BY next_operation;"""

    def add_next_action(row):
        mice = []
        for mouse in row:
            mouse = dict(mouse)
            last_procedure = db.session.query(Procedures).filter(Procedures.mouse_id==mouse['mouse_id'], ~Procedures.finished).order_by(desc(Procedures.id)).first()
            if last_procedure and last_procedure.name:
                mouse['action'] = "Current step is " + last_procedure.name
                next_step = Steps.query.filter(Steps.procedure_id==last_procedure.id).order_by(desc(Steps.id)).first()
                # next_step = Functions[last_procedure.name](mouse['mouse_id'], next_step_only=True)
                if next_step:
                    mouse['next_step'] = next_step.name
                else:
                    mouse['next_step'] = Steps_names[last_procedure.name][0]
                    
            else:
                last_procedure = db.session.query(Procedures).filter(Procedures.mouse_id==mouse['mouse_id']).order_by(desc(Procedures.id)).first()
                if last_procedure.name:
                    mouse['next_step'] = 'action'
                    mouse['action'] = "Just finished " + last_procedure.name
            mouse['next_operation'], mouse['color'] = time_display(mouse['next_operation'].date() - datetime.today().date())
            mice.append(mouse)
        return mice
            

    if request.method=='POST':
        if 'irats_id' in request.form:
            irats_id = request.form['irats_id']
            todo_mice = db.engine.execute(text(todo_mice_sql + """AND irats_id='""" + str(irats_id) + """'""" +  order_by_sql)).all()
            ids = [mouse.mouse_id for mouse in todo_mice]
            todo_mice = add_next_action(todo_mice)
            euthanized_mice = Mice.query.filter(Mice.irats_id==irats_id, ~ Mice.id.in_(ids), and_(Mice.euthanized!=None, Mice.euthanized==True)).order_by(desc(Mice.id))
            licenced_mice = Mice.query.filter(Mice.experiment!=None, Mice.irats_id==irats_id, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
            all_mice = Mice.query.filter(Mice.experiment==None, Mice.irats_id==irats_id, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
            #print(all_mice[0].euthanized)
            

        elif 'cage' in request.form:
            cage = request.form['cage']
            todo_mice = db.engine.execute(text(todo_mice_sql + """AND cage='""" + str(cage) + """'""" + order_by_sql)).all()
            ids = [mouse.mouse_id for mouse in todo_mice]
            todo_mice = add_next_action(todo_mice)
            euthanized_mice = Mice.query.filter(Mice.cage==cage, ~ Mice.id.in_(ids), and_(Mice.euthanized!=None, Mice.euthanized==True)).order_by(desc(Mice.id))
            licenced_mice = Mice.query.filter(Mice.experiment!=None, Mice.cage==cage, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
            all_mice = Mice.query.filter(Mice.experiment==None, Mice.cage==cage, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))


    else:
        user_id = session.get('user_id')
        user = Users.query.filter(Users.id==user_id).first()
        if show_all and user.admin_rights:
            todo_mice = db.engine.execute(text(todo_mice_sql +  order_by_sql)).all()
        else:
            user_name = user.full_name
            todo_mice = db.engine.execute(text(todo_mice_sql + """AND investigator='""" + str(user_name) + """'""" +  order_by_sql)).all()
        ids = [mouse.mouse_id for mouse in todo_mice]
        todo_mice = add_next_action(todo_mice)
        licenced_mice = Mice.query.filter(Mice.experiment!=None, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True), Mice.investigator==user.full_name).order_by(desc(Mice.id))
        euthanized_mice = []
        all_mice = [] 


    return render_template('mouse/index.html', todo_mice=todo_mice, licenced_mice=licenced_mice, all_mice=all_mice, euthanized_mice=euthanized_mice, now=datetime.today().date())

@bp.route("/full_index", methods=('GET', 'POST'))
@login_required
def full_index():
    return index(show_all=True)
    
@bp.route("/reload", methods=('GET', 'POST'))
@login_required
def reload():
    # download_user_projects(3)
    # download_licences()
    irats_fetch()
    return redirect(url_for('mouse.index'))

@bp.route("/search/<string:box>")
def process(box):
    query = request.args.get('query')
    if box == 'id':
        mice = Mice.query.filter(func.lower(Mice.irats_id).contains(query.lower()))
        suggestions = [{'value': mouse.irats_id, 'data':mouse.irats_id} for mouse in mice]
    if box == 'cage':
        mice = Mice.query.filter(Mice.cage.contains(query)).distinct(Mice.cage)
        suggestions = [{'value': mouse.cage, 'data':mouse.cage} for mouse in mice]
    if box == 'virus':
        viruses = Viruses.query.filter(Viruses.name.contains(query))
        suggestions = [{'value': virus.name, 'data':virus.name} for virus in viruses]
    if box == 'euthanasia':
        euthanasia_ways = ['Pentorbital', 'CO2', 'Dislocation']
        euthanasia = [way for way in euthanasia_ways if query.lower() in way.lower()]
        suggestions = [{'value': way, 'data':way} for way in euthanasia]
    if box == 'action':
        actions = ['Injection Surgery', 'Implantation Surgery', 'Protein Expression Check', 'Baseplating', 'Food scheduling', 'Euthanasia']
        actions = [action for action in actions if query.lower() in action.lower()]
        suggestions = [{'value': action, 'data':action} for action in actions]
    if box == 'coordinates':
        coordinates = Coordinates.query.filter(Coordinates.name.contains(query))
        suggestions = [{'value': cor.name, 'data':cor.name} for cor in coordinates]
    return jsonify({"suggestions":suggestions})

def get_mouse(id):
    mouse = Mice.query.filter(Mice.id==id).first()

    if mouse is None:
        abort(404, "Mouse id {0} doesn't exist.".format(id))

    return mouse

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    mouse = get_mouse(id)

    if request.method == 'POST':
        cage = request.form['cage']
        licence = request.form['licence']
        error = None

        if not cage:
            error = 'Cage Number is required.'

        if not licence:
            error = 'Licence is required.'

        if error is not None:
            flash(error)
        else:
            mouse.cage = cage
            mouse.licence = licence
            db.session.commit()
            return redirect(url_for('mouse.index'))

    return render_template('mouse/update.html', mouse=mouse)


@bp.route('/<int:id>/summary', methods=('GET', 'POST'))
@login_required
def mouse_summary(id):
    mouse = get_mouse(id)
    summary=[]
    procedures= Procedures.query.filter(Procedures.mouse_id==id).all()
    for procedure in procedures:
        procedure_dict = {'name':procedure.name,'steps':[]}
        steps = Steps.query.filter(Steps.procedure_id==procedure.id).order_by(asc(Steps.id)).all()
        for step in steps:
            user = Users.query.filter(Users.id==step.user_id).first()
            step_dict = {'name':step.name, 'user':user.full_name, 'comment':step.comment, 'entries':[]}
            entries = Entries.query.filter(Entries.step_id==step.id).all()
            for entry in entries:
                content = interprete(entry, display_mode=True)
                if content is not None:
                    entry_dict = {'name':entry.name, 'content':content}
                    step_dict['entries'].append(entry_dict)
            procedure_dict['steps'].append(step_dict)
        summary.append(procedure_dict)

    return render_template('mouse/summary.html', mouse=mouse, procedures=summary)

# @bp.route('/<int:id>/delete', methods=('POST',))
# @login_required
# def delete(id):
#     mouse = get_mouse(id)
#     db.session.delete(mouse)
#     db.session.commit()
#     return redirect(url_for('mouse.index'))