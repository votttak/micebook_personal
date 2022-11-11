###
# in short: when one clicks on the button "All mice" or "Index" one gets the mice list the users is working with. The mice info and correspondig options are the done with this code. 
# The corresponding frontend is mouse/index.html
###


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
bp = Blueprint('euthanized', __name__)

def time_display(delta):
    days = delta.days
    if days >0:
        return 'in '+str(days)+' days', "color: green"
    elif days==0:
        return 'today', "color: orange"
    else:
        return str(abs(days))+' days ago', "color: red"

@bp.route('/euthanized', methods=('GET', 'POST'))
@login_required
def index(show_all=True):
    def add_next_action(row):
        mice = []
        for mouse in row:
            mouse = dict(mouse)
            last_procedure = db.session.query(Procedures).filter(Procedures.mouse_id==mouse['mouse_id'], ~Procedures.finished).order_by(desc(Procedures.id)).first()
            if last_procedure and last_procedure.name:
                mouse['action'] = "Current step is " + last_procedure.name
                next_step = Steps.query.filter(Steps.procedure_id==last_procedure.id).order_by(desc(Steps.id)).first()
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

    todo_mice_sql = """SELECT *, TO_TIMESTAMP(step.content, 'YYYY-MM-DD"T"HH24:MI') + step.next_entry_in AS next_operation FROM mice JOIN (SELECT DISTINCT ON (mouse_id) *FROM ( SELECT *FROM steps JOIN      (SELECT  *FROM      entries WHERE  id in (SELECT MAX(id) FROM entries WHERE next_entry_in IS NOT NULL GROUP BY step_id)) e ON (e.step_id = steps.id) ) AS lastentries ORDER BY mouse_id, step_id DESC) step ON (mice.id=step.mouse_id) WHERE mice.id not in (SELECT mouse_id FROM steps WHERE name = 'Euthanasia') """
    order_by_sql =    """ ORDER BY next_operation;"""

    if request.method=='POST':
        print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_1111111111111111111111111111")
        if 'irats_id' in request.form:
            
            todo_mice = []
            ids = []
            euthanized_mice = Mice.query.filter(~ Mice.id.in_(ids), and_(Mice.euthanized!=None, Mice.euthanized==True)).order_by(desc(Mice.id)).all()
            licenced_mice = Mice.query.filter(Mice.experiment == None, ~ Mice.id.in_(ids), Mice.euthanized!=None, Mice.euthanized==True).order_by(desc(Mice.id))
            all_mice = Mice.query.filter(Mice.experiment == None, ~ Mice.id.in_(ids), Mice.euthanized!=None, Mice.euthanized==True).order_by(desc(Mice.id))
            

        elif 'cage' in request.form:
            
            cage = request.form['cage']
            todo_mice = db.engine.execute(text(todo_mice_sql + """AND cage='""" + str(cage) + """'""" + order_by_sql)).all()
            ids = [mouse.mouse_id for mouse in todo_mice]
            todo_mice = add_next_action(todo_mice)
            euthanized_mice = Mice.query.filter(Mice.cage==cage, ~ Mice.id.in_(ids), and_(Mice.euthanized!=None, Mice.euthanized==True)).order_by(desc(Mice.id))
            licenced_mice = Mice.query.filter(Mice.experiment!=None, Mice.cage==cage, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
            all_mice = Mice.query.filter(Mice.experiment==None, Mice.cage==cage, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
    
    
    # if request.method=='POST':
    #     print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_1111111111111111111111111111")

    #     print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_2222222222222222222222222222")
    #     # todo_mice = db.engine.execute(text(todo_mice_sql + """AND euthanized=True""" +  order_by_sql)).all()
    #     irats_id = request.form['irats_id']
    #     todo_mice = db.engine.execute(text(todo_mice_sql + """AND irats_id='""" + str(irats_id) + """'""" +  order_by_sql)).all()
    #     print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_2222222222222222222222222222_0000000000000000000000000")
    #     print(todo_mice)
    #     ids = [mouse.mouse_id for mouse in todo_mice]
    #     todo_mice = add_next_action(todo_mice)
        
    #     print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_3333333333333333333333333333")
    #     print(todo_mice)
    #     print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_3333333333333333333333333333_222222222222222222222222222")

    #     euthanized_mice = Mice.query.filter(~Mice.id.in_(ids), and_(Mice.euthanized != None, Mice.euthanized==True)).order_by(desc(Mice.id)).all()
    #     euthanized_mice = add_next_action(euthanized_mice)
    #     print(euthanized_mice)
    #     # licenced_mice = Mice.query.filter(Mice.experiment!=None, Mice.irats_id==irats_id, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
    #     # all_mice = Mice.query.filter(Mice.experiment==None, Mice.irats_id==irats_id, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True)).order_by(desc(Mice.id))
            

        

    else:
        print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_44444444444444444444444444444444")
        user_id = session.get('user_id')
        user = Users.query.filter(Users.id==user_id).first()
        if show_all and user.admin_rights:
            todo_mice = db.engine.execute(text(todo_mice_sql +  order_by_sql)).all()
        else:
            user_name = user.full_name
            todo_mice = db.engine.execute(text(todo_mice_sql + """AND investigator='""" + str(user_name) + """'""" +  order_by_sql)).all()
        ids = [mouse.mouse_id for mouse in todo_mice]
        print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_55555555555555555555555555555555555")
        todo_mice = add_next_action(todo_mice)
        print(todo_mice[0])
        print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK_66666666666666666666666666666666666")
        licenced_mice = Mice.query.filter(Mice.experiment!=None, ~ Mice.id.in_(ids), or_(Mice.euthanized==None, Mice.euthanized!=True), Mice.investigator==user.full_name).order_by(desc(Mice.id))
        euthanized_mice = []
        all_mice = []

    unique_room_ids = set()
    rooms_to_exclude = ['WAF F114 (OHB)', 'WAF G141 (EXP)', 'Y55F33']
    mouses = Mice.query.all()
    for mouse in mouses:
        if mouse.room_id is None:
            unique_room_ids.add("Empty")
        else:
            if mouse.room_id in rooms_to_exclude:
                continue
            unique_room_ids.add(mouse.room_id)

    unique_room_ids = sorted(unique_room_ids)


    ### put at top list User mices ### 
    user_id = user_id = session.get('user_id')
    user_name = Users.query.filter(Users.id==user_id).first().full_name

    non_user_mices_index = []
    todo_mice_sorted = []
    for i, mice in enumerate(todo_mice):
        if mice['investigator'] == user_name:
            todo_mice_sorted.append(mice)
        else: 
            non_user_mices_index.append(i)

    for i in non_user_mices_index:
        todo_mice_sorted.append(todo_mice[i])

    return render_template('mouse/euthanized.html', todo_mice=todo_mice_sorted, licenced_mice=licenced_mice, all_mice=all_mice, euthanized_mice=euthanized_mice, now=datetime.today().date(), unique_room_ids=unique_room_ids)

