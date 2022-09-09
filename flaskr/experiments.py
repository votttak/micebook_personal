
###
# When one created an experiment (sequence of actions) a user goes through the experiment created, 
# this file is for the process of going though an experiment designed. Yes, it's comlex!
# The corresponding frontend is eperiments.html
###

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy.sql.functions import current_user
import flask_sqlalchemy
from werkzeug.exceptions import ServiceUnavailable, abort
from flaskr.auth import login_required
from flask import Flask, json, jsonify
from . import db, Mice
from sqlalchemy import desc
from sqlalchemy import engine
from .tables import *
bp = Blueprint('experiments', __name__)
from .experiment_trees import next_procedure, next_step
from datetime import datetime, timedelta
# from dateutil import tz
from .external_communications import Load_Viruses, interprete, download_licences, download_user_projects, write_advance_transfer, read_severity, download_licences_and_projects
from sqlalchemy import func
from pathlib import Path
import os
from sys import platform

irats_update = False #Put to true to activate writing data back to Irast (Mouse in experiment, Project, severity, ...)


@bp.route("/<int:id>/reload_licences", methods=('GET', 'POST'))
@login_required
def reload_licences(id):
    download_licences()
    return redirect(url_for('experiments.design_experiment', id=id))



@bp.route("/<int:id>/reload_projects", methods=('GET', 'POST'))
@login_required
def reload_projects(id):
    user_id = session.get('user_id')
    download_user_projects(user_id)
    return redirect(url_for('experiments.design_experiment', id=id))



@bp.route("/<int:id>/reload_licences_and_projects", methods=('GET', 'POST'))
@login_required
def reload_licences_and_projects(id):
    user_id = session.get('user_id')
    download_licences_and_projects(user_id)
    return redirect(url_for('experiments.design_experiment', id=id))



def minimize(name):
    template_name = ""
    for a in name.lower().split(" "):
        template_name += a + "_"
    template_name = template_name[:-1]
    return(template_name)   


def get_mouse(id):
    mouse = Mice.query.filter(Mice.id==id).first()

    if mouse is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    return mouse


def upload_entries_to_form(form, step_id):
    entries = Entries.query.filter(Entries.step_id==step_id).all()
    if entries==[]:
        return "HERE_HERE_1"
        return None
    for field in form:
        if not 'value' in field:
            # aisi: if no "type" field, set "type" to 'text'
            if 'type' in field:
                type =  field['type']    
            else: 
                type = 'text'
            
            values = []
            # aisi: handle list of types
            if type=='multiple':
                for subfield in field['fields']:
                    for entry in entries:
                        if entry.name==subfield['id']:  
                            subfield['value'] = entry.content
                            entries.remove(entry)              
            # aisi: if a single type
            else:
                for entry in entries:
                    if entry.name==field['name']:
                        values.append(entry.content)
                        entries.remove(entry)
                if len(values):
                    if type=="bool" or type=='checkbox':
                        for choice in field['choices']:
                            for value in values:
                                if value==str(choice['value']):
                                    choice['checked'] = True
                                else:               
                                    choice['checked'] = False
                    elif 'hours_precision' in field:
                        if len(values[-1].split(":"))<2:
                            full_time = values[-1]+":00"
                            field['value'] = full_time
                    else:
                        field['value'] = values[-1]

    extra_values = []
    for entry in entries: #left entries not in input forms => can belong to scoring
        extra_values.append({'name':entry.name, 'value':entry.content})
    return extra_values


def default_time_value(form): #Adds a default time (current time) to datetime fields (prevents IOS platforms bug)
    for field in form:
        if (field['type']=="datetime-local") and ('value' not in field):
            field['value'] = datetime.now().strftime("%Y-%m-%dT%H:%M")


# display(args, reload_step=current_step, buffer=buffer_only)
def display(args, reload_step=None, buffer=False):
    comment_value = ""

    # Reload all step entries in the case the user is going back to check entries again
    if reload_step:
        form = args['forms']
        scoring_values = upload_entries_to_form(form, reload_step.id)
        comment_value = reload_step.comment
        if not comment_value:
            comment_value =""

    default_time_value(form) 
    # Just return arguments as a buffer in case we want to load multiple mice forms in parallel
    if buffer:
        return args
    else:
        
        return render_template('actions/experiment.html', **args, comment_value=comment_value, step=reload_step.id, scoring_values=scoring_values)   



@bp.route('/<int:id>/previous_step', methods=('GET', 'POST')) 
@login_required
def go_back(id): ### Change to extract last entry and go directly to experiment without url redirect with a go_back/update argument
    current_step = Steps.query.filter(Steps.mouse_id==id).order_by(desc(Steps.id)).first()
    # current_procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first() 
    previous_step = Steps.query.filter(Steps.mouse_id==id, Steps.id <current_step.id).order_by(desc(Steps.id)).first()
    if not previous_step:
        flash('Cannot go back')
        procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first() 
        return redirect(url_for('experiments.'+minimize(procedure.name), id=id, step_id=current_step.id))    
    else:
        procedure = Procedures.query.filter(Procedures.id==previous_step.procedure_id).first() 
        return redirect(url_for('experiments.'+minimize(procedure.name), id=id, step_id=previous_step.id))            
    


@bp.route('/get_last_weight/<int:mouse_id>', methods=('GET', 'POST'))
@login_required
def get_last_weight(mouse_id):
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id).subquery()
    weight_entry = db.session.query(Entries).filter(Entries.step_id.in_(actions),  Entries.reference_weight).order_by(desc(Entries.id)).first()
     
    if weight_entry:
        if weight_entry.content:
            weight = float(weight_entry.content)
            return jsonify({"lastweight":weight})
        else:
            db.session.delete(weight_entry)
            db.session.commit()
            return get_last_weight(mouse_id)
    else:
        return jsonify({"lastweight":None})



def get_last_ref_weight(mouse_id):
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id).subquery()
    weight_entry = db.session.query(Entries).filter(Entries.step_id.in_(actions),  Entries.reference_weight).order_by(desc(Entries.id)).first() 
    if weight_entry:
        if weight_entry.content:

            return float(weight_entry.content)
        else:
            db.session.delete(weight_entry)
            db.session.commit()
            return get_last_ref_weight(mouse_id)
    else:
        return "HERE_HERE_2"
        return None

def ketmaine_xylazine_from_previous_step(mouse_id):
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id).subquery()
    anesthetic_entry = db.session.query(Entries).filter(Entries.step_id.in_(actions),  Entries.name == "Anesthetic").order_by(desc(Entries.id)).first() 
    if anesthetic_entry:
        if anesthetic_entry.content:
            if anesthetic_entry.content == 'Ketamine & Xylazine':
                return True
            else:
                return False


@bp.route('/get_virus_construct/<virus_name>', methods=('GET', 'POST'))
@login_required
def get_virus_construct(virus_name):
    # TODO: check wether virus_name in Viruses.name
    virus_construct_entry = db.session.query(Viruses).filter(Viruses.name == virus_name).first()    
    if virus_construct_entry.construct:
        virus_construct = str(virus_construct_entry.construct)
        return jsonify({"virus construct" : virus_construct})
    else:
        return "HERE_HERE_3"
        return None



@bp.route('/get_coordinates_by_name/<coordinates_name>', methods=('GET', 'POST'))
@login_required
def get_coordinates_by_name(coordinates_name):
    # TODO: check wether virus_name in Viruses.name
    coordinates_entry = db.session.query(Coordinates).filter(Coordinates.name == coordinates_name).first()
    
    ap_coordinate = str(coordinates_entry.AP)
    ml_coordinate = str(coordinates_entry.ML)
    dv_coordinate = str(coordinates_entry.DV)
    
    if not(ap_coordinate and ml_coordinate and dv_coordinate):
        return "HERE_HERE_4"
        return None
    else: 
        return jsonify({"ap_coordinate": ap_coordinate, "ml_coordinate": ml_coordinate, "dv_coordinate": dv_coordinate})
    


def get_last_time_schedule(mouse_id, current_step):
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id, Steps.id<current_step.id).subquery()
    last_time = Entries.query.filter(Entries.step_id.in_(actions), Entries.next_entry_in.isnot(None)).order_by(desc(Entries.id)).first()
    if last_time:
        return last_time
    else:
        return "HERE_HERE_5"
        return None    

# remark: this weight is not reference_weight, this one is used for dosierung calculations 
def get_last_weight_for_drug_dosierung(mouse_id): 
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id).subquery()
    # weights = db.session.query(Entries).filter(Entries.step_id.in_(actions),  Entries.name == "Bodyweight (grams)").order_by(desc(Entries.id)).all()
    weight = db.session.query(Entries).filter(Entries.step_id.in_(actions), Entries.name == "Bodyweight (grams)").order_by(desc(Entries.id)).first()
    if weight:
        pass
        # print(weight.name)
        # print(weight.content)
    


@bp.route('/<int:id>/update_severity_to_next', methods=('GET', 'POST'))
@login_required
def update_severity_to_next(id):
    return _update_severity(id, next=True)



@bp.route('/<int:id>/update_severity_to_index', methods=('GET', 'POST'))
@login_required
def update_severity_to_index(id):
    return _update_severity(id, next=False)


def _update_severity(id, next=False):
    print("FUNCTION:_updata_severity")
    mouse = get_mouse(id)
    severity= mouse.severity

    if request.method == 'POST':
        new_severity = request.form['severity']
        if not (new_severity == severity):
            mouse.severity = new_severity
            db.session.commit()
            written = write_advance_transfer(id, severity=new_severity, complete=irats_update)
            if not written:
                flash("Mouse couldn't be found on the PDA interface and thus information have not been updated theReload Mice fLoad_Miceom Iratsre. Please verify the mouse ID on Irats and Reload Mice. The update of the mouse severity needs to be done manually.")

        if next:
            return redirect(url_for('experiments.start_experiment', id=id))
        else:
            return redirect(url_for('mouse.index'))

    
    return render_template('actions/severity.html', mouse=mouse, current_severity=severity, severity_status=["Not in experiment", "0", "1", "2", "3"])


def readout(forms, step, entries_dicts, next_step_args=None, extra_entries = None, severity=False):

    if isinstance(forms, dict):
        forms = forms.to_dict(flat=True)
    if extra_entries:
        forms.update(extra_entries)
    
    #Prepare next step if there isn't already a created next step for this procedure
    if next_step_args:
        next_step = Steps.query.filter(Steps.procedure_id==step.procedure_id, Steps.name==next_step_args['name'], Steps.id>step.id).first()
        if not next_step: 
            next_step_args.update({'user_id':session['user_id']})
            next_step = Steps(**next_step_args) 
            db.session.add(next_step)
            db.session.commit()
    
    if 'comment' in forms:
        step.comment = forms.pop('comment')
    step.new = False
    
    ### Delete possible previous entries if step gets rewritten
    delete_entries = Entries.__table__.delete().where(Entries.step_id == step.id)
    db.session.execute(delete_entries)

    # Define next page to load based on type of submit in form
    if 'direction' in forms:
        direction = forms.pop('direction')
    else:
        direction = 'index'

    if direction=='skip':
        step.comment="Skipped"
        db.session.commit()

    elif not (direction in ['next', 'index', 'nothing']): # corresponds to special directions
        inputs = {'step_id':step.id}
        inputs['content'] = True
        inputs['name'] = direction
        inputs['entry_format'] = 'bool'
        db.session.add(Entries(**inputs))
        db.session.commit()  

    else:
        # Maps filled values to form dictionaries and then create corresponding Entries in Database
        for id in forms:
            if forms[id]:
                inputs = {'step_id':step.id}
                inputs['content'] = forms[id]
                inputs['name'] = id
                inputs['entry_format'] = "text"
                for entry_dict in entries_dicts:
                    if id == entry_dict['id']:
                        inputs['name'] = entry_dict['name']
                        inputs['entry_format'] = entry_dict['type']
                        if 'next_entry_in' in entry_dict:
                            inputs['next_entry_in'] = entry_dict['next_entry_in']
                        if 'reference_weight' in entry_dict:
                            inputs['reference_weight'] = entry_dict['reference_weight']
                        if 'hours_precision' in entry_dict:
                            inputs['entry_format'] = "datehour"
                            hour_time = forms[id].split(":")[0]
                            minutes = forms[id].split(":")[1]
                            if float(minutes)>=30:
                                trunc_hours = hour_time.split("T")[-1]
                                hours = int(trunc_hours) + 1
                                hour_time = hour_time.split("T")[0] + "T" + str(hours)
                            inputs['content'] = hour_time
                        break
                db.session.add(Entries(**inputs))
        db.session.commit()


    if direction == 'nothing':
        global last_id
        global last_step_id
        global last_url
        return redirect(url_for(last_url, id=last_id, step_id=last_step_id))

    # Redirects to next page
    if not severity:
        if direction == 'next':
            return redirect(url_for('experiments.start_experiment', id=step.mouse_id))
        else:
            return redirect(url_for('mouse.index'))
    else:
        if direction == 'next':
            return redirect(url_for('experiments.update_severity_to_next', id=step.mouse_id))
        else:
            return redirect(url_for('experiments.update_severity_to_index', id=step.mouse_id))




## get the experiment from the database according "id" ##
def get_experiment(id):
    experiment = Experiments.query.filter(Experiments.id==id).first()
    if experiment is None:
        abort(404, "Experimnet id {0} doesn't exist.".format(id))
    return experiment


## deleting experiment ## 
@bp.route('/<int:experiment_id>/<int:mouse_id>/delete_experiment', methods=('GET', 'POST'))
@login_required
def delete_experiment(experiment_id, mouse_id):
    experiment = get_experiment(experiment_id)
    print(experiment_id)
    db.session.delete(experiment)
    db.session.commit()
    
    # return redirect(url_for('virus.index'))
    # return redirect(url_for('actions.experiment_choice'))
    # return redirect(url_for('http://127.0.0.1:5000/1436/choose_experiment'))
    return redirect(url_for('experiments.choose_experiment', id=mouse_id))



@bp.route('/<int:id>/choose_experiment', methods=('GET', 'POST'))
@login_required
def choose_experiment(id):
    mouse = get_mouse(id)

    user_id = session.get('user_id')
    experiments = Experiments.query.filter(Experiments.user_id==user_id).all()
    experiments_list = []
    for experiment in experiments:
        actions = Experiment_actions.query.filter(Experiment_actions.experiment_id==experiment.id).all()
        length = db.session.query(func.max(Experiment_actions.index)).filter(Experiment_actions.experiment_id==experiment.id).first()[0]
        action_list = [[] for _ in range(length+1)]
        for action in actions:
            action_list[action.index].append(action.name)
        project = Projects.query.filter(Projects.id==experiment.project_id).first()
        if project:
            experiment_dict = {'id':experiment.id, 'name':experiment.name, 'actions':action_list, 'project':project.name}
            experiments_list.append(experiment_dict)
        else:
            experiment_dict = {'id': experiment.id, 'name': experiment.name, 'actions':action_list}
            experiments_list.append(experiment_dict)            

    
    

    if request.method == 'POST':
        experiment_id = int(request.form['experiment'])
        experiment = Experiments.query.filter(Experiments.id==experiment_id).first()
        project = Projects.query.filter(Projects.id==experiment.project_id).first()
        licence = Licences.query.filter(Licences.id==project.licence_id).first()
        project_name = project.name.split(licence.number)[-1].split("-")[-1]
        written = write_advance_transfer(id, licence=licence.number, project=project_name, status='In experiment', severity='0', complete=irats_update)
        if not written:
            flash("Mouse couldn't be found on the PDA interface and thus information have not been updated there. Please verify the mouse ID on Irats and Reload Mice. The update of the mouse project needs to be done manually.")
        mouse.experiment = experiment_id
        mouse.severity = "0"
        db.session.commit()
        return redirect(url_for('experiments.start_experiment', id=id))

    
    return render_template('actions/experiment_choice.html', mouse=mouse, experiments=experiments_list)





InjS_Scoring = ['Day1/1', 'Day1/2', 'Day2/1', 'Day2/2', 'Day3/1', 'Day3/2', 'Day4', 'Day5', 'Day6', 'Day7']
InjS_Scoring_Delays = [timedelta(days=0), timedelta(days=1), timedelta(days=0), timedelta(days=1), timedelta(days=0), timedelta(days=1), timedelta(days=1), timedelta(days=1), timedelta(days=1), timedelta(days=7)]
Post_InjS_weighting = [True, False, True, False, True, False, True, True, True, True] #Days when weighting the mouse is required
injection_surgery_steps = ['Pre-surgical Scoring', 'Surgery Setup', 'Surgery Protocol', 'Post-surgery Scoring']
@bp.route('/<int:id>/injection_surgery/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def injection_surgery(id, step_id):
    setup_global_vars(id, step_id, 'experiments.injection_surgery')
    return _injection_surgery(id,step_id)


def _injection_surgery(id, step_id, buffer_only=False): #experiment
    steps_names = injection_surgery_steps
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    injection = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    # get_last_weight_for_drug_dosierung(mouse.id)
    print(request.form)
    if current_step.name == steps_names[0]:
        pre_surgical_score_forms = [{'name':"Score", 'id':"score", 'type':"int"}, {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)}]

        if request.method == 'POST':        
            if not request.form['Bodyweight (grams)']:      
                flash('Mouse weight measurement required (in score)')       
                args = {'mouse':mouse, 'page_name':"Pre-surgical Injection Scoring", 'forms':pre_surgical_score_forms, 'scoring':True}      
                return display(args, reload_step=current_step, buffer=buffer_only)      

            pre_surgical_score_forms.append({'name': 'Bodyweight (grams)', 'id': "Bodyweight (grams)", 'type':"float", 'reference_weight':True})

            next_step_args = {'name':steps_names[1], 'mouse_id':id, 'procedure_id':injection.id}    
            print(00)
            print(request.form)
            return readout(request.form, current_step, pre_surgical_score_forms, next_step_args)    


        args = {'mouse':mouse, 'page_name':"Pre-surgical Injection Scoring", 'forms':pre_surgical_score_forms, 'scoring':True}  
        return display(args, reload_step=current_step, buffer=buffer_only)  

    elif current_step.name == steps_names[1]:

        if platform=="win32":
            virus_csv_filename = os.path.join(Path().resolve().parents[0], "Virus_List.csv")
        else:
            virus_csv_filename = "/var/www/mfabre/webapp/Virus_List.csv"
        Load_Viruses(virus_csv_filename, db, Viruses)
        
        surgery_setup = [
        {'name':"Time", 'id':"pre_bu", 'type':"datetime-local"}, 
        {'name':"Anesthetic", 'id':"anesthetic", 'type':"bool", 'choices':[{'id':"ket", 'name':"Ketamine & Xylazine", 'value':"Ketamine & Xylazine", 'checked':True}, {'id':"isoflurane", 'name':"Isoflurane", 'value':"Isoflurane"}]}, 
        ]
  
        ### VIRUS FIELDS ###
        class VirusBlock:
            def __init__(self, virus_block_id: str, inputs:list):
                self.class_name = virus_block_id[:-1]
                self.block_id = virus_block_id
                self.inputs = inputs
        
        viruses_setup = [ VirusBlock("virus_block{}".format(i), [
            {'name':"Virus {}".format(i), 'id':"virus{}".format(i), 'type':"virus",'not_required':True, 'block':"virus_block_{}".format(i)}, 
            {'name':"Virus {} construct".format(i), 'id': "virus_construct{}".format(i), 'type': "virus", 'fetch_data': True, 'block':"virus_block_{}".format(i)}, 
            {'name':"Coordinates name for Virus {} (optional)".format(i), 'id':"coordinates{}".format(i), 'type':"virus", 'not_required':True, 'block':"virus_block_{}".format(i)},
            {'name':"Coordinates Virus {} (AP/ML/DV)".format(i), 'id':"coord{}".format(i), 'type':"virus", 'secondary_type':"multiple", 'block':"virus_block_{}".format(i), 
                    'fields':[
                        {'id':"AP Coordinate Virus {}".format(i)}, 
                        {'id':"ML Coordinate Virus {}".format(i)}, 
                        {'id':"DV Coordinate Virus {}".format(i)},
                        ], 'not_required':True}, 
            
            {'name':"Virus {} Volume (nL)".format(i), 'id':"virus{}_vol".format(i), 'type':"virus", 'not_required':True, 'block':"virus_block_{}".format(i)},
            {'name':"Virus {} ratio".format(i), 'id':"virus_ratio{}".format(i), 'type':"virus", 'not_required':True},
            {'name':"Virus {} Injection speed (nL/min)".format(i), 'id':"virus_inj_speed{}".format(i), 'type':"virus"}, 
            {'name':"Virus {} Post-injection waiting (minutes)".format(i), 'id':"virus_waiting{}".format(i), 'type':"virus"}
            ]) for i in range(0, 10) ]
        
        ### IMPLANTATION FIELDS ###
        class ImplantationBlock:
            def __init__(self, implantation_block_id: str, inputs:list):
                self.class_name = implantation_block_id[:-1]
                self.block_id = implantation_block_id
                self.inputs = inputs

        implantations_setup = [ ImplantationBlock("implantation_block{}".format(i), [
            {'name':"Coordinates name for Implantation {} (optional)".format(i), 'id':"coordinates_implantation{}".format(i), 'type':"virus", 'not_required':True, 'block':"virus_block_{}".format(i)},
            {'name':"Implantation Coordinates {} (AP/ML/DV)".format(i), 'id':"coord{}".format(i), 'type':"virus", 'not_required':True, 'block':"implantation_block_{}".format(i), 'secondary_type':"multiple", 'fields':[{'id':"AP Coordinate Implantation {}".format(i)}, {'id':"ML Coordinate Implantation {}".format(i)}, {'id':"DV Coordinate Implantation {}".format(i)}]}, 
            {'name': "Implantation {} Type".format(i), 'secondary_type': "tickboxes",        'choices':[{'name':"Cranial window (CW)", 'id':"cw_{}".format(i), 'value':"CW_{}".format(i)}, {'name':"Cannula", 'id':"cannula_{}".format(i), 'value':"Cannula_{}".format(i)}, {'name':"Fibre", 'id':"fibre_{}".format(i), 'value':"Fibre_{}".format(i)}, {'name':"Electrode", 'id':"electrode_{}".format(i), 'value':"Electrode_{}".format(i)}], 'type':"checkbox"}
            # {'name':"Pre-emptive Analgesia", 'choices':[{'name':"BU",                  'id':"bu", 'value':"BU"}, {'name':"CA", 'id':"ca", 'value':"CA"}],                                                                                                                                                'type':"checkbox"}
            ]) for i in range(0, 10) ]

        
        weight_from_scoring = get_last_ref_weight(mouse.id)
        surgery_setup_page = [{'name':"Pre-emptive Analgesia", 'weight': weight_from_scoring, 'choices':[{'name':"BU", 'id':"bu_pre_emptive", 'value':"BU"}, {'name':"CA", 'id':"ca_pre_emptive", 'value':"CA"}], 'type':"checkbox"}] + surgery_setup.copy()
        surgery_setup += [{'name':"Pre-emptive Analgesia", 'id':"bu", 'type':"text"}, {'name':"Pre-emptive Analgesia", 'id':"ca", 'type':"text"}] #, {'name':"AP Coordinate", 'id':"AP", 'type':"float"}, {'name':"ML Coordinate", 'id':"ML", 'type':"float"}, {'name':"DV Coordinate", 'id':"DV", 'type':"float"}]

        if request.method == 'POST':
            next_step_args = {'name':steps_names[2], 'mouse_id':id, 'procedure_id':injection.id}
            return readout(request.form, current_step, surgery_setup, next_step_args)

        args = {'mouse':mouse, 'page_name':"Injection Surgery Setup", 'forms':surgery_setup_page, 'viruses': viruses_setup, 'add_virus_btn_required' : True, 'implantations':implantations_setup}
        return display(args, reload_step=current_step, buffer=buffer_only)
        

    elif current_step.name == steps_names[2]:

        weight_from_scoring = get_last_ref_weight(mouse.id)
        anesthetic_ketamine_and_xylazine = ketmaine_xylazine_from_previous_step(mouse.id)
        print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV")
        print(weight_from_scoring)
        print("VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV")
        surgery_protocol = [
            # {'name':"Anesthetic Injection Time", 'id':"inj_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}, 
            {'name':"Anesthetic Induction Time", 'id':"inj_time", 'analgesia_amount': weight_from_scoring*0.01, 'anesthetic': anesthetic_ketamine_and_xylazine, 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}, 
            {'name':"Lidocain", 'id':"lido", 'weight': weight_from_scoring, 'type':"bool", 'choices':[{'id':"yes", 'name':"Yes", 'value':"True"}, {'id':"no", 'name':"No", 'value':"False", 'checked':True}]},
            {'name':"End of Surgery", 'id':"surg_end", 'type':"datetime-local"},
            {'name':"Wake-up Time", 'id':"wakeup_time", 'type':"datetime-local"}, 
            {'name':"Post-surgical BU", 'id':"post_bu", 'type':"datetime-local"}
            ] 
            

        surgery_setup = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[1]), Steps.procedure_id==injection.id).order_by(desc(Steps.id)).first()
        setup_entries = Entries.query.filter(Entries.step_id == surgery_setup.id).all()
        setup_reminder = [] 
        CoordinateVirus1 = [""]*3
        CoordinateVirus2 = [""]*3
        
        for entry in setup_entries:
            if entry.name=="Time":
                min_surg_time = interprete(entry) + timedelta(minutes=20)
                max_surg_time = interprete(entry) + timedelta(hours=4)
                early_surg = min_surg_time.strftime("%I:%M%p")
                min_surg_time = min_surg_time.strftime("%Y-%m-%dT%H:%M")
                max_surg_time = max_surg_time.strftime("%Y-%m-%dT%H:%M")
                setup_reminder.append({'name':"Earlist surgery time", 'value':early_surg})
            elif entry.name=="Anesthetic":
                if "Ketamine" in interprete(entry):
                    weight = get_last_ref_weight(id)
                    if weight:
                        injection_volume = str(0.01*float(weight))+' ml' 
                        setup_reminder.append({'name':"Ketamine volume to inject", 'value':injection_volume})
        
            elif entry.name=="Virus":
                virus_name = interprete(entry)
                setup_reminder.append({'name':entry.name, 'value':virus_name})
                virus = Viruses.query.filter(Viruses.name==virus_name).first()
                setup_reminder.append({'name':"Virus promoter", 'value':virus.promoter})
                setup_reminder.append({'name':"Virus expressing protein", 'value':virus.expressing_protein})
                setup_reminder.append({'name':"Virus dependency", 'value':virus.dependency})
            elif entry.name=="Virus 2":
                if interprete(entry):
                    virus_name = interprete(entry)
                    setup_reminder.append({'name':entry.name, 'value':virus_name})
                    virus = Viruses.query.filter(Viruses.name==virus_name).first()
                    setup_reminder.append({'name':"Virus promoter", 'value':virus.promoter})
                    setup_reminder.append({'name':"Virus expressing protein", 'value':virus.expressing_protein})
                    setup_reminder.append({'name':"Virus dependency", 'value':virus.dependency})
            elif entry.name=="AP Coordinate Virus 1":
                CoordinateVirus1[0] = entry.content
            elif entry.name=="ML Coordinate Virus 1":
                CoordinateVirus1[1] = entry.content
            elif entry.name=="DV Coordinate Virus 1":
                CoordinateVirus1[2] = entry.content
            elif entry.name=="AP Coordinate Virus 2":
                CoordinateVirus2[0] = entry.content
            elif entry.name=="ML Coordinate Virus 2":
                CoordinateVirus2[1] = entry.content
            elif entry.name=="DV Coordinate Virus 2":
                CoordinateVirus2[2] = entry.content
            elif interprete(entry):
                print(setup_reminder)
                

                def get_time_from_entries_for_bu_ca(ents):
                    entries_interpreted = [interprete(ent) for ent in ents]
                    bu_and_ca = ("BU" in entries_interpreted) and ("CA" in entries_interpreted)
                    bu_and_not_ca = ("BU" in entries_interpreted) and (not ("CA" in entries_interpreted))
                    not_bu_and_ca = (not ("BU" in entries_interpreted)) and ("CA" in entries_interpreted)
                    
                    if bu_and_ca:
                        return entries_interpreted[2]
                    elif bu_and_not_ca or not_bu_and_ca: 
                        return entries_interpreted[1]
                    else:
                        # means we don't need time for BU or CA
                        return False

                time_for_bu_ca = get_time_from_entries_for_bu_ca(setup_entries)
                if time_for_bu_ca:
                    setup_reminder.append({'name':entry.name, 'value':interprete(entry) + " [Injection time: " + str(time_for_bu_ca) + "]"})
                else:
                    setup_reminder.append({'name':entry.name, 'value':interprete(entry)})
                print(setup_reminder)

        if "".join(CoordinateVirus1) != "":
            setup_reminder.append({'name':"Coordinates (AP/ML/DV) Virus 1", 'value':"/".join(CoordinateVirus1)})
        if "".join(CoordinateVirus2) != "":
            setup_reminder.append({'name':"Coordinates (AP/ML/DV) Virus 2", 'value':"/".join(CoordinateVirus2)})

        

        surgery_protocol[0]['min'] = min_surg_time
        surgery_protocol[0]['max'] = max_surg_time



        if request.method == 'POST':
            next_step_args = {'name': steps_names[3]+'_'+InjS_Scoring[0], 'mouse_id':id, 'procedure_id':injection.id}
            print()
            print(22)
            print()
            print(request.args)
            print()
            print(request.form)
            print()
            print(request.values)
            return readout(request.form, current_step, surgery_protocol, next_step_args, severity=True)
            

        

        
        args = {'mouse':mouse, 'page_name':"Injection Surgery Protocol", 'forms':surgery_protocol, 'display':setup_reminder, 'display_title':"Surgery info"}
        return display(args, reload_step=current_step, buffer=buffer_only)

    else:
        
        

        if not ('Day' in current_step.name): # not initialized post-surgery scoring
            current_step.name = current_step.name+'_'+InjS_Scoring[0]
            db.session.commit()

        # Extract next scoring day informationsF
        name = current_step.name.split('_')[-1]
        index = InjS_Scoring.index(name)
        time_to_next = InjS_Scoring_Delays[index]
        if index == len(InjS_Scoring)-1:
            # If we are at the last day, mark the procedure as finished
            injection.finished = True
            db.session.commit()
            next_scoring = None # No next step
        else:
            next_scoring = InjS_Scoring[index+1]
        if index >=6: #Find if we can skip this scoring or not
            skipped = db.session.query(Steps).filter(Steps.mouse_id==id, Steps.id<current_step.id, Steps.name.contains(steps_names[3]), Steps.procedure_id==injection.id, Steps.comment=="Skipped").count()
            if skipped<2:
                skippable=True
            else:
                skippable = False
        else:
            skippable = False


        post_surgical_scoring =  [{'name':"Score", 'id':"score", 'type':"int"}, 
        {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':time_to_next}]
        post_surgical_scoring_page = post_surgical_scoring.copy() + [{'name':"Analgesia", 'choices':[{'name':"BU", 'id':"bu", 'value':"BU"},{'name':"CA", 'id':"ca", 'value':"CA"}], 'type':"checkbox"}]
        post_surgical_scoring += [{'name':"Analgesia", 'id':"bu", 'type':"text"}, {'name':"Analgesia", 'id':"ca", 'type':"text"}]

        surgery = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[2]), Steps.procedure_id==injection.id).order_by(desc(Steps.id)).first()
        # injection_entry = Entries.query.filter(Entries.step_id==surgery.id, Entries.name=='Anesthetic Injection Time').first()
        injection_entry = Entries.query.filter(Entries.step_id==surgery.id, Entries.name=='Anesthetic Induction Time').first()
        inj_time = datetime.strptime(injection_entry.content, "%Y-%m-%dT%H:%M") 
        now = datetime.now()
        args = {'mouse':mouse, 'page_name':'Injection Surgery Scoring for ' + InjS_Scoring[index], 'forms':post_surgical_scoring_page, 'last_action':'Injection', 'time':inj_time, 'now':now, 'scoring':True, 'skippable':skippable}

        if request.method == 'POST':    
            scoring_time_entry = None
            if request.form['direction']=='skip':
                scorings = db.session.query(Steps.id).filter(Steps.mouse_id==id, Steps.name.contains('Scoring'), Steps.procedure_id==injection.id, Steps.name.contains('Day'), Steps.id<current_step.id).subquery()
                last_score_time = Entries.query.filter(Entries.step_id.in_(scorings), Entries.next_entry_in.isnot(None)).order_by(desc(Entries.id)).first()
                scoring_time_entry = {'score_time':(interprete(last_score_time)+last_score_time.next_entry_in).strftime("%Y-%m-%dT%H:%M")} # Get a virtual score time to match the skipped day
            elif Post_InjS_weighting[index]:
                if not request.form['Bodyweight (grams)']:
                    flash('Mouse weight measurement required (in score)')
                    return display(args, reload_step=current_step, buffer=buffer_only)

            if next_scoring:
                next_step_args = {'name': steps_names[3]+'_' + next_scoring, 'mouse_id':id, 'procedure_id':injection.id}
                severity = False
            else:
                next_step_args = None
                severity = True
            return readout(request.form, current_step, post_surgical_scoring, next_step_args, extra_entries=scoring_time_entry, severity=severity)

        return display(args, reload_step=current_step, buffer=buffer_only)





ImpS_Scoring = ['Day1/1', 'Day1/2', 'Day2/1', 'Day2/2', 'Day3/1', 'Day3/2', 'Day4', 'Day5', 'Day6', 'Day7']
ImpS_Scoring_Delays =  [timedelta(days=0), timedelta(days=1), timedelta(days=0), timedelta(days=1), timedelta(days=0), timedelta(days=1), timedelta(days=1), timedelta(days=1), timedelta(days=1), timedelta(days=7)]





implantation_surgery_steps = ['Pre-surgical Scoring', 'Surgery Setup', 'Surgery Protocol', 'Post-surgery Scoring']
# Vadim
surgery_steps = ["Vadim_1", "Vadim_2"]



last_id = None
last_step_id = None
last_url = None

def setup_global_vars(id, step_id, url):
    global last_id
    global last_step_id
    global last_url

    last_step_id = step_id
    last_id = id
    last_url = url

Post_ImpS_weighting = [True, False, True, False, True, False, True, True, True, True]
@bp.route('/<int:id>/implantation_surgery/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def implantation_surgery(id, step_id):
    setup_global_vars(id, step_id, 'experiments.implantation_surgery')
    return _implantation_surgery(id, step_id)

def _implantation_surgery(id, step_id, buffer_only=False): #experiment
    steps_names = implantation_surgery_steps
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    implantation = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()
   
    if current_step.name == steps_names[0]:

        pre_surgical_score_forms = [{'name':"Score", 'id':"score", 'type':"int"}, {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)}]


        if request.method == 'POST':
            if not request.form['Bodyweight (grams)']:
                flash('Mouse weight measurement required (in score)')
                args = {'mouse':mouse, 'page_name':"Pre-surgical Implantation Scoring", 'forms':pre_surgical_score_forms, 'scoring':True}
                return display(args, reload_step=current_step, buffer=buffer_only) 

            next_step_args = {'name':steps_names[1], 'mouse_id':id, 'procedure_id':implantation.id}
            pre_surgical_score_forms.append({'name': 'Bodyweight (grams)', 'id': "Bodyweight (grams)", 'type':"float", 'reference_weight':True})
            return readout(request.form, current_step, pre_surgical_score_forms, next_step_args)

        args = {'mouse':mouse, 'page_name':"Pre-surgical Implantation Scoring", 'forms':pre_surgical_score_forms, 'scoring':True}
        return display(args, reload_step=current_step, buffer=buffer_only)   

    elif current_step.name == steps_names[1]:

        surgery_setup = [{'name':"Time", 'id':"pre_bu", 'type':"datetime-local"}, {'name':"Anesthetic", 'id':"anesthetic", 'type':"bool", 'choices':[{'id':"ket", 'name':"Ketamine & Xylazine", 'value':"Ketamine & Xylazine", 'checked':True}, {'id':"isoflurane", 'name':"Isoflurane", 'value':"Isoflurane"}]},
        {'name':"Coordinates (AP/ML/DV)", 'id':"coord", 'type':"multiple", 'fields':[{'id':"AP Coordinate"}, {'id':"ML Coordinate"}, {'id':"DV Coordinate"}]}]
        surgery_setup_page = [{'name':"Pre-emptive Analgesia", 'choices':[{'name':"BU", 'id':"bu", 'value':"BU"},{'name':"CA", 'id':"ca", 'value':"CA"}], 'type':"checkbox"}] + surgery_setup.copy()
        surgery_setup += [{'name':"Pre-emptive Analgesia", 'id':"bu", 'type':"text"}, {'name':"Pre-emptive Analgesia", 'id':"ca", 'type':"text"}] #, {'name':"AP Coordinate", 'id':"AP", 'type':"float"}, {'name':"ML Coordinate", 'id':"ML", 'type':"float"}, {'name':"DV Coordinate", 'id':"DV", 'type':"float"}]
        # surg_setup = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[1]), Steps.procedure_id==implantation.id).order_by(desc(Steps.id)).first()
        # if not surg_setup:


        if request.method == 'POST':
            next_step_args = {'name':steps_names[2], 'mouse_id':id, 'procedure_id':implantation.id}
            return readout(request.form, current_step, surgery_setup, next_step_args)

        args = {'mouse':mouse, 'page_name':"Implantation Surgery Setup", 'forms':surgery_setup_page}
        return display(args, reload_step=current_step, buffer=buffer_only)    

    elif current_step.name == steps_names[2]:

        surgery_protocol = [{'name':"Anesthetic Injection Time", 'id':"imp_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}, {'name':"Lidocain", 'id':"lido", 'type':"bool", 'choices':[{'id':"yes", 'name':"Yes", 'value':"True"}, {'id':"no", 'name':"No", 'value':"False", 'checked':True}]},
        {'name':"End of Surgery", 'id':"surg_end", 'type':"datetime-local"},
        {'name':"Wake-up Time", 'id':"wakeup_time", 'type':"datetime-local"}, {'name':"Post-surgical BU", 'id':"post_bu", 'type':"datetime-local"}]

    # surgery = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[2]), Steps.procedure_id==implantation.id).order_by(desc(Steps.id)).first()
    # if not surgery:

        surgery_setup = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[1]), Steps.procedure_id==implantation.id).order_by(desc(Steps.id)).first()
        setup_entries = Entries.query.filter(Entries.step_id == surgery_setup.id).all()
        setup_reminder = []
        Coordinate = [""]*3
        for entry in setup_entries:
            if entry.name=="Time":
                min_surg_time = interprete(entry) + timedelta(minutes=20)
                max_surg_time = interprete(entry) + timedelta(hours=4)
                early_surg = min_surg_time.strftime("%I:%M%p")
                min_surg_time = min_surg_time.strftime("%Y-%m-%dT%H:%M")
                max_surg_time = max_surg_time.strftime("%Y-%m-%dT%H:%M")
                setup_reminder.append({'name':"Earlist surgery time", 'value':early_surg})
            elif entry.name=="Anesthetic":
                if "Ketamine" in interprete(entry):
                    weight = get_last_ref_weight(id)
                    if weight:
                        injection_volume = str(0.01*float(weight))+' ml' 
                        setup_reminder.append({'name':"Ketamine volume to inject", 'value':injection_volume})
            elif entry.name=="AP Coordinate":
                Coordinate[0] = entry.content
            elif entry.name=="ML Coordinate":
                Coordinate[1] = entry.content
            elif entry.name=="DV Coordinate":
                Coordinate[2] = entry.content
            elif interprete(entry):
                setup_reminder.append({'name':entry.name, 'value':interprete(entry)})

        if "".join(Coordinate)!="":
            setup_reminder.append({'name':"Coordinates (AP/ML/DV)", 'value':"/".join(Coordinate)})

        surgery_protocol[0]['min']=min_surg_time
        surgery_protocol[0]['max']=max_surg_time


        if request.method == 'POST':
            next_step_args = {'name':steps_names[3]+'_'+InjS_Scoring[0], 'mouse_id':id, 'procedure_id':implantation.id}
            return readout(request.form, current_step, surgery_protocol, next_step_args, severity=True)

        
        return render_template('actions/experiment.html', mouse=mouse, page_name="Implantation Surgery Protocol", forms=surgery_protocol, display=setup_reminder, display_title="Surgery info") 


    else:

        if not ('Day' in current_step.name): # not initialized post-surgery scoring
            current_step.name = current_step.name+'_'+ImpS_Scoring[0]
            db.session.commit()

        # Extract next scoring day informations
        name = current_step.name.split('_')[-1]
        index = ImpS_Scoring.index(name)
        time_to_next = ImpS_Scoring_Delays[index]
        if index == len(ImpS_Scoring)-1:
            # If we are at the last day, mark the procedure as finished
            implantation.finished = True
            db.session.commit()
            next_scoring = None # No next step
        else:
            next_scoring = ImpS_Scoring[index+1]
        if index >=6: #Find if we can skip this scoring or not
            skipped = db.session.query(Steps).filter(Steps.mouse_id==id, Steps.id<current_step.id, Steps.name.contains(steps_names[3]), Steps.procedure_id==implantation.id, Steps.comment=="Skipped").count()
            # scorings = db.session.query(Steps.id).filter(Steps.mouse_id==id, Steps.name.contains(steps_names[3]), Steps.procedure_id==implantation.id).subquery()
            # skipped = db.session.query(Entries).filter(Entries.step_id.in_(scorings), Entries.name=='Skipped').count() 
            if skipped<2:
                skippable=True
            else:
                skippable = False
        else:
            skippable = False



        post_surgical_scoring =  [{'name':"Score", 'id':"score", 'type':"int"}, 
        {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':time_to_next}]
        post_surgical_scoring_page = [{'name':"Analgesia", 'choices':[{'name':"BU", 'id':"bu", 'value':"BU"},{'name':"CA", 'id':"ca", 'value':"CA"}], 'type':"checkbox"}] + post_surgical_scoring.copy()
        post_surgical_scoring += [{'name':"Analgesia", 'id':"bu", 'type':"text"}, {'name':"Analgesia", 'id':"ca", 'type':"text"}]

        surgery = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(steps_names[2]), Steps.procedure_id==implantation.id).order_by(desc(Steps.id)).first()
        implantation = Entries.query.filter(Entries.step_id==surgery.id, Entries.name=='Anesthetic Injection Time').first()
        imp_time = datetime.strptime(implantation.content, "%Y-%m-%dT%H:%M") 
        now = datetime.now()
        args = {'mouse':mouse, 'page_name':'Implantation Surgery Scoring for ' + InjS_Scoring[index], 'forms':post_surgical_scoring_page, 'last_action':'Implantation', 'time':imp_time, 'now':now, 'scoring':True, 'skippable':skippable}


        if request.method == 'POST':   
            scoring_time_entry = None
            if request.form['direction']=='skip':
                scorings = db.session.query(Steps.id).filter(Steps.mouse_id==id, Steps.name.contains('Post-surgery Scoring'), Steps.procedure_id==implantation.id, Steps.id<current_step.id).subquery()
                last_score_time = Entries.query.filter(Entries.step_id.in_(scorings), Entries.next_entry_in.isnot(None)).order_by(desc(Entries.id)).first()
                scoring_time_entry = {'score_time':(interprete(last_score_time)+last_score_time.next_entry_in).strftime("%Y-%m-%dT%H:%M")}
            elif Post_ImpS_weighting[index]:
                if not request.form['Bodyweight (grams)']:
                    flash('Mouse weight measurement required (in score)')
                    return display(args, reload_step=current_step, buffer=buffer_only)

            if next_scoring:
                next_step_args = {'name': steps_names[3]+'_' + next_scoring, 'mouse_id':id, 'procedure_id':implantation.id}
                severity = False
            else:
                next_step_args = None
                severity = True
            return readout(request.form, current_step, post_surgical_scoring, next_step_args, extra_entries=scoring_time_entry, severity=severity)

        return display(args, reload_step=current_step, buffer=buffer_only)


def get_time_if_in_db(step_id, input_name):
        time_to_restore = Entries.query.filter(Entries.step_id == step_id, Entries.name == input_name).first()
        if time_to_restore is None:
            return ""
        return time_to_restore.content


protein_expression_check_steps = ['Weekly Expression Check']
@bp.route('/<int:id>/Protein_Expression_Check/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def protein_expression_check(id, step_id):
    setup_global_vars(id, step_id, 'experiments.protein_expression_check')
    return _protein_expression_check(id, step_id)

def _protein_expression_check(id, step_id, buffer_only=False):
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    protein_check = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()
    step_name = protein_expression_check_steps[0] +'_Week '

    # last_check_result = Entries.query.filter(Entries.step_id==current_step.id, Entries.name=='Good to go to next step').order_by(desc(Entries.id)).first()
    # if (last_check_result.content=='False'):
    #     week = int(last_check.name.split(" ")[-1]) + 1
    #     if week > 6:

    if not '_Week' in current_step.name:
        current_step.name += '_Week 1'
    week = int(current_step.name.split(" ")[-1])
    if week >=6:
        flash('6 weeks or more without passed expression check: You should euthanize mouse.')

    health_expression_check = [{'name':"Score", 'id':"score", 'type':"int"}, 
    {'name':"Protein Expressed", 'value_name':"Expression Quality", 'id':"prot", 'type':'range', 'min':0, 'max':10}, 
    {'name':"Check hour", 'id':"check_time", 'type':"datetime-local", 'hours_precision':True, 'value': get_time_if_in_db(step_id, "Check hour"), 'next_entry_in':timedelta(days=7)}, 
    {'name':"Good to go to next step", 'id':"good", 'type':"bool", 'choices':[{'id':"yes", 'name':"Yes", 'value':"True"}, {'id':"no", 'name':"No", 'value':"False", 'checked':True}]}]


    if request.method == 'POST':
        if request.form['good'] and request.form['good']=="True":
            protein_check.finished=True
            db.session.commit()
            next_step_args = None
            severity = True
        else:
            next_step_args = {'name':step_name+str(week+1), 'mouse_id':id, 'procedure_id':protein_check.id}
            severity = False
        health_expression_check.append({'name': 'Bodyweight (grams)', 'id': "Bodyweight (grams)", 'type':"float", 'reference_weight':True})
        return readout(request.form, current_step, health_expression_check, next_step_args, severity=severity)

    args = {'mouse':mouse, 'page_name':"Scoring & Protein Expression Check", 'forms':health_expression_check, 'scoring':True}
    return display(args, reload_step=current_step, buffer=buffer_only)   
        


baseplating_steps = ['Baseplating']
@bp.route('/<int:id>/Baseplating/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def baseplating(id, step_id):
    setup_global_vars(id, step_id, 'experiments.baseplating')
    return _baseplating(id, step_id)

def _baseplating(id, step_id, buffer_only=False):
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    baseplating_time = [{'name':"Score", 'id':"score", 'type':"int"}, 
                        # {'name':"Baseplating hour", 'id':"baseplate", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)},
                        {'name':"Anesthetic", 'bodyweight_from_same_page': True,  'id':"anesthetic", 'type':"bool", 'choices':[{'id':"ket", 'name':"Ketamine & Xylazine", 'value':"Ketamine & Xylazine", 'checked':True}, {'id':"isoflurane", 'name':"Isoflurane", 'value':"Isoflurane"}]},
                        {'name':"Anesthetic Induction Time", 'id':"inj_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=7)},
                        {'name':"End of Baseplating", 'id':"surg_end", 'type':"datetime-local"},
                        {'name':"Wake-up Time", 'id':"wakeup_time", 'type':"datetime-local"}
                        ]

    if request.method == 'POST':
        procedure.finished=True
        db.session.commit()

        return readout(request.form, current_step, baseplating_time)

    args = {'mouse':mouse, 'page_name':"Record Baseplating", 'forms':baseplating_time}
    return display(args, reload_step=current_step, buffer=buffer_only)   



        
scheduling_steps = ['Initial Scoring', 'Scheduling Initialization', 'Scheduling Experiment']
food_scheduling_fixed_amount_steps = scheduling_steps
food_scheduling_fixed_time_steps = scheduling_steps
water_scheduling_steps = scheduling_steps
@bp.route('/<int:id>/Food_Scheduling_fixed_amount/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def food_scheduling_fixed_amount(id, step_id):
    setup_global_vars(id, step_id, 'experiments.food_scheduling_fixed_amount')
    return _food_scheduling_fixed_amount(id, step_id)

def _food_scheduling_fixed_amount(id, step_id, buffer_only=False):
    return _scheduling(id, step_id, buffer_only=buffer_only, type=0)

@bp.route('/<int:id>/Food_Scheduling_fixed_time/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def food_scheduling_fixed_time(id, step_id):
    setup_global_vars(id, step_id, 'experiments.food_scheduling_fixed_time')
    return _food_scheduling_fixed_time(id, step_id)

def _food_scheduling_fixed_time(id, step_id, buffer_only=False):
    return _scheduling(id, step_id, buffer_only=buffer_only, type=1)

@bp.route('/<int:id>/Water_Scheduling/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def water_scheduling(id, step_id):
    setup_global_vars(id, step_id, 'experiments.water_scheduling')
    return _water_scheduling(id, step_id)

def _water_scheduling(id, step_id, buffer_only=False):
    return _scheduling(id, step_id, buffer_only=buffer_only, type=2)

# return redirect(url_for('experiments.update_severity_to_next',id=id))

def _scheduling(id, step_id, buffer_only=False, type=0): 

    print("AABBCC_start")
    print(id)
    print(step_id)
    print(buffer_only)
    print(type)
    print("AABBCC_end")

    '''
    type: 0 for food scheduling with controlled volume, 
    1 for food scheduling just with introducion time,
    2 for water scheduling
    '''
    mouse = get_mouse(id)
    scheduling_names = ['Food Scheduling fixed amount', 'Food Scheduling fixed time', 'Water Scheduling']
    scheduling_functions = ['experiments.food_scheduling_fixed_amount', 'experiments.food_scheduling_fixed_time', 'experiments.water_scheduling']
    scheduling_operations = ['Food introduction', 'Food delivering', 'Water delivering']


    scheduling_name = scheduling_names[type]
    scheduling_function = scheduling_functions[type]
    scheduling_operation = scheduling_operations[type]

    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    print("QQQQQQQQQQQQQQQQQQQQQQQQQQQ")
    print(scheduling_steps)
    print(current_step)
    print(current_step.name)
    print(scheduling_steps[1])
    print(scheduling_steps[1] in current_step.name)
    print(scheduling_steps[0])
    print(scheduling_steps[0] in current_step.name)
    print("type: " + str(type))

    if current_step.name == scheduling_steps[0]:

        pre_food_scheduling_score_forms = [
            {'name':"Score", 'id':"score", 'type':"int"}, 
            {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)}]

        if request.method == 'POST':
            if not request.form['Bodyweight (grams)']:
                flash('Mouse weight measurement required')
                args = {'mouse':mouse, 'page_name':"Initial "+scheduling_name+" Scoring", 'forms':pre_food_scheduling_score_forms, 'scoring':True}
                return display(args, reload_step=current_step, buffer=buffer_only)          

            next_step_args = {'name':scheduling_steps[1]+'_Day 1', 'mouse_id':id, 'procedure_id':procedure.id}
            pre_food_scheduling_score_forms.append({'name': 'Bodyweight (grams)', 'id': "Bodyweight (grams)", 'type':"float", 'reference_weight':True})
            return readout(request.form, current_step, pre_food_scheduling_score_forms, next_step_args=next_step_args, severity=True)

        args = {'mouse':mouse, 'page_name':"Initial "+scheduling_name+" Scoring", 'forms':pre_food_scheduling_score_forms, 'scoring':True}
        return display(args, reload_step=current_step, buffer=buffer_only)   

    elif scheduling_steps[1] in current_step.name:
        print("AVA")
        print(current_step.name)
        init_weight = get_last_ref_weight(id)
        if type==0:
            weight_target = 0.9*init_weight
            extreme_weight = 0.85*init_weight
            weight_target_message = "90% Weight Target is "+str(weight_target)+"g"
            daily_food = round(weight_target*3.84/25, 2)
        elif type==1:
            weight_target = 0.9*init_weight
            extreme_weight = 0.85*init_weight
            weight_target_message = "90% Weight Target is "+str(weight_target)+"g"
            daily_food=None
        elif type==2:
            weight_target = 0.85*init_weight
            extreme_weight = 0.8*init_weight
            weight_target_message = "85% Weight Target is "+str(weight_target)+"g"
            daily_food=None
        
        step_name = scheduling_steps[1]


        if type==0:
            scheduling_initialization_forms = [
                # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                {'name':"Score", 'id':"score", 'type':"int"}, 
                {'name':"Food collected during experiment (grams)", 'id':"food_collected", 'type':"float"}, 
                {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"}, 
                {'name':"Extra food given (grams)", 'id':"food_given", 'type':"float"}, 
                {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)},
                # {'name':"Is animal ready for experiment?", 'id':"ready", 'type':'bool', 'choices':[{'id':"yes", 'name':"Yes", 'value':True}, {'id':"no", 'name':"No", 'value':False, 'checked':True}]}
                ]
        elif type==1:
            scheduling_initialization_forms = [
                # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                {'name':"Score", 'id':"score", 'type':"int"}, 
                {'name':"Food collected during experiment (grams)", 'id':"food_collected", 'type':"float"}, 
                {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"}, 
                {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)},
            # {'name':"Is animal ready for experiment?", 'id':"ready", 'type':'bool', 'choices':[{'id':"yes", 'name':"Yes", 'value':True}, {'id':"no", 'name':"No", 'value':False, 'checked':True}]}
            ]
        elif type==2:
            scheduling_initialization_forms = [
                # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                {'name':"Score", 'id':"score", 'type':"int"},
                {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"}, 
                {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)},
            # {'name':"Is animal ready for experiment?", 'id':"ready", 'type':'bool', 'choices':[{'id':"yes", 'name':"Yes", 'value':True}, {'id':"no", 'name':"No", 'value':False, 'checked':True}]}
            ]


        previous_step = Steps.query.filter(Steps.procedure_id==procedure.id, Steps.id<step_id).order_by(desc(Steps.id)).first()
        ad_libitum_option = True # Allow to use ad libitum in current step
        if "Ad Libitum" in current_step.name:
            scheduling_initialization_forms = [{'name':"Number of ad libitum days", 'id':"ad_libitum_days", 'type':"float"}]
            page_name = scheduling_name+" Ad Libitum"
            last_experiment_day = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.name.contains('Day'), Steps.procedure_id==procedure.id, Steps.id<current_step.id).order_by(desc(Steps.id)).first()
            if last_experiment_day:
                day = int(last_experiment_day.name.split(" ")[-1])
            else:
                day=1
        
        
            #### TO BE IMPLEMENTED
        elif "Weight Reinitialization" in current_step.name:
            scheduling_initialization_forms = [{'name':"post_ad_libitum", 'id':"post_ad_libitum", 'type':"info", 'value':"Reinitialize bodyweight after ad libitum "}, {'name':"Bodyweight (grams)", 'id':"weight", 'type':"float", 'reference_weight':True}]
            page_name = scheduling_name+" Weight Reinitialization"
            init_weight = None
            weight_target = None
            weight_target_message = None
            daily_food = None  
            ad_libitum_option = False

            last_experiment_day = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.name.contains('Day'), Steps.procedure_id==procedure.id, Steps.id<current_step.id).order_by(desc(Steps.id)).first()
            if last_experiment_day:
                day = int(last_experiment_day.name.split(" ")[-1])
            else:
                day=0

        elif "Weight Reinitialization" in previous_step.name:

            day = int(current_step.name.split(" ")[-1])
            page_name=scheduling_name+" Check Day "+str(day)

        else:
            last_food_collected = interprete(Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Food collected during experiment (grams)').order_by(desc(Entries.id)).first())
            last_food_given = interprete(Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Extra food given').order_by(desc(Entries.id)).first())
            if last_food_collected and last_food_given:
                daily_food = last_food_collected + last_food_given

            last_check_weight = Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Pre-session weight (grams)').order_by(desc(Entries.id)).first()
            if last_check_weight:
                last_weight = float(last_check_weight.content)
                loss = str(100-last_weight/init_weight*100)+'%'


            day = int(current_step.name.split(" ")[-1])
            page_name=scheduling_name+" Check Day "+str(day)

            # if day!=1:
            #     checks = db.session.query(Steps.id).filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.procedure_id==procedure.id, Steps.id<current_step.id).subquery()
            #     introduction_time = interprete(db.session.query(Entries).filter(Entries.step_id.in_(checks),  Entries.name==scheduling_operation+' time').order_by(desc(Entries.id)).first())
            #     info = scheduling_operation+" at " + introduction_time.strftime("%I:%M%p") + " (+/- 1 hour)"
            #     scheduling_initialization_forms.remove({'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)})
            #     scheduling_initialization_forms = [{'name':scheduling_operation+" time", 'id':"introduction_time_info", 'type':"info", 'value':info}] + scheduling_initialization_forms
        


        
        '''
        if day>14:
            flash('Initialization going for more than 2 weeks! Euthanize mouse.')
        '''

        if request.method == 'POST':
            extra_entry = None
            if request.form['direction'] and request.form['direction']=="end":
                procedure.finished = True
                db.session.commit()   
                next_step_args = None
                
            else:
            
                if "ready" in request.form and request.form['ready']=="True": # In case experimenter wants to go to the main experiment part
                    next_step_name = scheduling_steps[2]+'_Day 1'
                else:
                    next_step_name = step_name+'_Day '+ str(day+1) # Just go to next day
                    
                if "Ad Libitum" in request.form or ("Ad Libitum" in current_step.name):
                    current_step.name = step_name+' Ad Libitum' # Ad libitum instead of planned scheduling day
                    db.session.commit()

                    next_step_name = step_name+' Weight Reinitialization'
                    num_days = int(request.form["ad_libitum_days"])
                    last_timing = get_last_time_schedule(id, current_step=current_step)
                    if last_timing: # Creates virtual time for ad libitum start to keep track of schedule
                        extra_entry = {'ad_libitum_time':(interprete(last_timing)+timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")}
                        scheduling_initialization_forms.append({'name':"Ad Libitum start time", 'id':"ad_libitum_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=num_days)})
                    scheduling_initialization_forms.append({'name':"Number of ad libitum days", 'id':"ad_libitum_days", 'type':"float"})
                elif not "introduction_time" in request.form: 
                    # Complete entries with an automated food introduction time based on previous one
                    scheduling_initialization_forms.append({'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)})
                    last_timing = get_last_time_schedule(id, current_step=current_step)
                    extra_entry={'introduction_time':(interprete(last_timing)+timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")}
                next_step_args = {'name':next_step_name, 'mouse_id':id, 'procedure_id':procedure.id}
            return readout(request.form, current_step, scheduling_initialization_forms, next_step_args=next_step_args , extra_entries=extra_entry)

        args = {'mouse':mouse, 
                'page_name':page_name,      
                'forms':scheduling_initialization_forms, 
                'weight_target_message':weight_target_message, 
                'food_amount': daily_food, 
                'scoring':True, 
                # 'scheduling':"pre_weight", 
                'soft_weight_target':weight_target, 
                'hard_weight_target':extreme_weight, 
                'ad_libitum':ad_libitum_option, 
                'enddable':True}
        return display(args, reload_step=current_step, buffer=buffer_only)   


    else:
        init_weight = get_last_ref_weight(id)
        if type==0:
            weight_target = 0.9*init_weight
            extreme_weight = 0.85*init_weight
            weight_target_message = "90% Weight Target is "+str(weight_target)+"g"
            daily_food = round(weight_target*3.84/25,2)
        elif type==1:
            weight_target = 0.9*init_weight
            extreme_weight = 0.85*init_weight
            weight_target_message = "90% Weight Target is "+str(weight_target)+"g"
            # daily_food = round(weight_target*3.84/25,2)
            daily_food=None
        elif type==2:
            weight_target = 0.85*init_weight
            extreme_weight = 0.8*init_weight
            # daily_food = round(weight_target*3.84/25,2)
            weight_target_message = "85% Weight Target is "+str(weight_target)+"g"
            daily_food=None

        step_name = scheduling_steps[2]
        page_name = scheduling_name + " Experiment"

        if type==0:
            scheduling_experiment_forms = [
                            # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                            {'name':"Score", 'id':"score", 'type':"int"}, 
                            {'name':"Food collected during experiment (grams)", 'id':"food_collected", 'type':"float"}, 
                            {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"}, 
                            {'name':"Extra food given (grams)", 'id':"food_given", 'type':"float"}, 
                            {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}]
        elif type==1:
            scheduling_experiment_forms = [
                            # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                            {'name':"Score", 'id':"score", 'type':"int"}, 
                            {'name':"Food collected during experiment (grams)", 'id':"food_collected", 'type':"float"}, 
                            {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"},     
                            {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}]
        elif type==2:
            scheduling_experiment_forms = [
                            # {'name':"Pre-session weight (grams)", 'id':"pre_weight", 'type':"float"}, 
                            {'name':"Score", 'id':"score", 'type':"int"},
                            {'name':"Post-session weight (grams)", 'id':"post_weight", 'type':"float"},     
                            {'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)}]

        previous_step = Steps.query.filter(Steps.procedure_id==procedure.id, Steps.id<step_id).order_by(desc(Steps.id)).first()
        print("Current step: " + current_step.name)
        print("Previous step: " + previous_step.name)
        ad_libitum_option = True # Allow to use ad libitum in current step
        if "Ad Libitum" in current_step.name:
            scheduling_experiment_forms = [{'name':"Number of ad libitum days", 'id':"ad_libitum_days", 'type':"float"}]
            page_name = scheduling_name+" Ad Libitum"
            last_experiment_day = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.name.contains('Day'), Steps.procedure_id==procedure.id, Steps.id<current_step.id).order_by(desc(Steps.id)).first()
            if last_experiment_day:
                day = int(last_experiment_day.name.split(" ")[-1])
            else:
                day=1
        elif "Weight Reinitialization" in current_step.name:
            scheduling_experiment_forms = [
                            {'name':"post_ad_libitum", 'id':"post_ad_libitum", 'type':"info", 'value':"Reinitialize bodyweight after ad libitum "}, 
                            {'name':"Bodyweight (grams)", 'id':"weight", 'type':"float", 'reference_weight':True}]
            page_name = page_name+" Weight Reinitialization"
            init_weight = None
            weight_target = None
            weight_target_message = None
            daily_food = None  
            ad_libitum_option = False

            last_experiment_day = Steps.query.filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.name.contains('Day'), Steps.procedure_id==procedure.id, Steps.id<current_step.id).order_by(desc(Steps.id)).first()
            if last_experiment_day:
                day = int(last_experiment_day.name.split(" ")[-1])
            else:
                day=0

        elif "Weight Reinitialization" in previous_step.name:

            day = int(current_step.name.split(" ")[-1])
            page_name=page_name+" Day "+str(day)

        else:
            last_food_collected = interprete(Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Food collected during experiment (grams)').order_by(desc(Entries.id)).first())
            last_food_given = interprete(Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Extra food given').order_by(desc(Entries.id)).first())
            if last_food_collected and last_food_given:
                daily_food = last_food_collected + last_food_given

            last_check_weight = Entries.query.filter(Entries.step_id==previous_step.id, Entries.name=='Pre-session weight (grams)').order_by(desc(Entries.id)).first()
            if last_check_weight:
                last_weight = float(last_check_weight.content)
                loss = str(100-last_weight/init_weight*100)+'%'
                    
            day = int(current_step.name.split(" ")[-1])
            page_name=scheduling_name+" Check Day "+str(day)

            if day!=1:
                checks = db.session.query(Steps.id).filter(Steps.mouse_id==id, Steps.name.contains(step_name), Steps.procedure_id==procedure.id, Steps.id<current_step.id).subquery()
                introduction_time = interprete(db.session.query(Entries).filter(Entries.step_id.in_(checks),  Entries.name==scheduling_operation+' time').order_by(desc(Entries.id)).first())
                info = scheduling_operation+" at " + introduction_time.strftime("%I:%M%p") + " (+/- 1 hour)"
                scheduling_experiment_forms.remove({'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)})
                scheduling_experiment_forms = [{'name':scheduling_operation+" time", 'id':"introduction_time_info", 'type':"info", 'value':info}] + scheduling_experiment_forms

        if day>56:
            flash('Initialization going for more than 2 weeks! Euthanize mouse.')

        if request.method == 'POST':
            extra_entry = None
            if request.form['direction'] and request.form['direction']=="end":
                procedure.finished = True
                db.session.commit()   
                next_step_args = None
                
            else:
                next_step_name = step_name+'_Day '+ str(day+1) # Just go to next day
                    
                if "Ad Libitum" in request.form or ("Ad Libitum" in current_step.name): 

                    current_step.name = step_name+' Ad Libitum' # Ad libitum instead of planned scheduling day
                    db.session.commit()

                    next_step_name = step_name+' Weight Reinitialization'
                    num_days = int(request.form["ad_libitum_days"])
                    last_timing = get_last_time_schedule(id, current_step=current_step)
                    if last_timing: # Creates virtual time for ad libitum start to keep track of schedule
                        extra_entry = {'ad_libitum_time':(interprete(last_timing)+timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")}
                        scheduling_experiment_forms.append({'name':"Ad Libitum start time", 'id':"ad_libitum_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=num_days)})
                    scheduling_experiment_forms.append({'name':"Number of ad libitum days", 'id':"ad_libitum_days", 'type':"float"})

                elif not "introduction_time" in request.form: 
                    # Complete entries with an automated food introduction time based on previous one
                    scheduling_experiment_forms.append({'name':scheduling_operation+" time", 'id':"introduction_time", 'type':"datetime-local", 'next_entry_in':timedelta(days=1)})
                    last_timing = get_last_time_schedule(id, current_step=current_step)
                    extra_entry={'introduction_time':(interprete(last_timing)+timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")}

                next_step_args = {'name':next_step_name, 'mouse_id':id, 'procedure_id':procedure.id}

            return readout(request.form, current_step, scheduling_experiment_forms, next_step_args=next_step_args , extra_entries=extra_entry)

        args = {'mouse':mouse, 'page_name':page_name, 'forms':scheduling_experiment_forms, 'weight_target_message':weight_target_message, 'food_amount': daily_food, 'scoring':True, 'scheduling':"pre_weight", 'soft_weight_target':weight_target, 'hard_weight_target':extreme_weight, 'ad_libitum':ad_libitum_option, 'enddable':True}
        return display(args, reload_step=current_step, buffer=buffer_only)  


non_scheduling_experiment_steps = ['Experiment Recording']
@bp.route('/<int:id>/Non_Scheduling_Experiment/<int:step_id>', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def non_scheduling_experiment(id, step_id):
    setup_global_vars(id, step_id, 'experiments.non_scheduling_experiment')
    return _non_scheduling_experiment(id, step_id)

def _non_scheduling_experiment(id, step_id, buffer_only=False):
    mouse = get_mouse(id)


    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    if current_step.name==non_scheduling_experiment_steps[0]:
        current_step.name+=" 1"
        db.session.commit()
        return redirect(url_for('experiments.update_severity_to_next',id=id))

    experiment_number = int(current_step.name.split(" ")[-1])

    experiment_forms = [ 
        {'name':"Score", 'id':"score", 'type':"int"}, 
        {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)},
        {'name':"experiment_info", 'id':"experiment_info", 'type':"info", 'value':"Score mouse and precise experiment protocol, length or other usefull information"}]


    if request.method == 'POST':
        print("8")
        if request.form['direction'] and request.form['direction']=="end":
            procedure.finished = True
            db.session.commit()   
            next_step_args = None

        else:
            # if not request.form['Bodyweight (grams)']:
            #     flash('Mouse weight measurement required')
            #     args = {'mouse':mouse, 'page_name':"Experiment Recording "+str(experiment_number), 'forms':experiment_forms, 'comment_required':True, 'enddable':True}
            #     print(7)
            #     return display(args, reload_step=current_step, buffer=buffer_only)  

            next_step_args = {'name':'Experiment Recording '+str(experiment_number+1), 'mouse_id':id, 'procedure_id':procedure.id}
            if experiment_number==1:
                experiment_forms.append({'name': 'Bodyweight (grams)', 'id': "Bodyweight (grams)", 'type':"float", 'reference_weight':True}) # Make the first weight a reference weight for scoring
        print(9)
        return readout(request.form, current_step, experiment_forms, next_step_args=next_step_args)

    args = {'mouse':mouse, 'page_name':"Experiment Recording "+str(experiment_number), 'forms':experiment_forms, 'comment_required':True, 'enddable':True}
    return display(args, reload_step=current_step, buffer=buffer_only)  

euthanasia_steps = ['Euthanasia']
@bp.route('/<int:id>/Euthanasia/<int:step_id>', methods=('GET', 'POST'))
@login_required
def euthanasia(id, step_id):
    setup_global_vars(id, step_id, 'experiments.euthanasia')
    return _euthanasia(id, step_id)

def _euthanasia(id, step_id, buffer_only=False): 
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    euthanasia_forms = [{'name':"Score", 'id':"score", 'type':"int"}, {'name':"Euthanasia method", 'id':"euthanasia", 'type':"text"}, {'name':"Euthanasia time", 'id':"score_time", 'type':"datetime-local"}]

    if request.method == 'POST':
        procedure.finished = True
        mouse.euthanized = True
        db.session.commit()
        return readout(request.form, current_step, euthanasia_forms, severity=True)

    args = {'mouse':mouse, 'page_name':"Euthanasia", 'forms':euthanasia_forms, 'not_euthanasia':True, 'comment_required':True, 'scoring':True, 'no_back':True}
    return display(args, reload_step=current_step, buffer=buffer_only)  

handling_steps = ['Handling']
@bp.route('/<int:id>/Handling/<int:step_id>', methods=('GET', 'POST')) 
@login_required
def handling(id, step_id):
    setup_global_vars(id, step_id, 'experiments.handling')
    return _handling(id, step_id)

def _handling(id, step_id, buffer_only=False): 
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    parallel_procedure = Procedures.query.filter(Procedures.id!=procedure.id, ~Procedures.finished).order_by(desc(Procedures.id)).first()
    priority_procedures = ['Injection Surgery', 'Implantation Surgery',  'Food Scheduling fixed amount', 'Food Scheduling fixed time', 'Water Scheduling', 'Non Scheduling Experiment']
    if parallel_procedure and (parallel_procedure.name in priority_procedures): # Handling should postpone next necessary scoring only when outside of a "priority" procedure
        handling_time_field = {'name':"Handling hour", 'id':"check_time", 'type':"datetime-local", 'hours_precision':True}
    else:
        handling_time_field = {'name':"Handling hour", 'id':"check_time", 'type':"datetime-local", 'hours_precision':True, 'next_entry_in':timedelta(days=7)}

    handling_check = [{'name':"Score", 'id':"score", 'type':"int"}, {'name':"Rate Mouse behavior", 'value_name':"Mouse tranquility", 'id':"behav", 'type':'range', 'min':0, 'max':10}, handling_time_field]

    if request.method == 'POST':
        procedure.finished = True
        db.session.commit()
        return readout(request.form, current_step, handling_check)

    args = {'mouse':mouse, 'page_name':"Handling", 'forms':handling_check}
    return display(args, reload_step=current_step, buffer=buffer_only)  

scoring_steps = ['Scoring']
@bp.route('/<int:id>/scoring/<int:step_id>', methods=('GET', 'POST')) 
@login_required
def scoring(id, step_id):
    setup_global_vars(id, step_id, 'experiments.scoring')
    return _scoring(id, step_id)
    
def _scoring(id, step_id, buffer_only=False):
    mouse = get_mouse(id)

    current_step = Steps.query.filter(Steps.id==step_id).first()
    procedure = Procedures.query.filter(Procedures.id==current_step.procedure_id).first()

    parallel_procedure = Procedures.query.filter(Procedures.id!=procedure.id, ~Procedures.finished).order_by(desc(Procedures.id)).first()
    priority_procedures = ['Injection Surgery', 'Food Scheduling fixed amount', 'Food Scheduling fixed time', 'Water Scheduling', 'Non Scheduling Experiment']
    if parallel_procedure and (parallel_procedure.name in priority_procedures): # Scoring should postpone next necessary scoring only when outside of a "priority" procedure
        scoring_time_field = {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local", 'hours_precision':True}
    else:
        scoring_time_field = {'name':"Scoring hour", 'id':"score_time", 'type':"datetime-local",'hours_precision':True, 'next_entry_in': timedelta(days=7)}

    scoring_forms =  [{'name':"Score", 'id':"score", 'type':"int"}, scoring_time_field]
    if request.method == 'POST':
        procedure.finished = True
        db.session.commit()
        return readout(request.form, current_step, scoring_forms)


    args = {'mouse':mouse, 'page_name':"Scoring", 'forms':scoring_forms}
    return display(args, reload_step=current_step, buffer=buffer_only)  



#### CHANGE WHEN NEW ACTIONS ADDED
# Vadim
Procedures_names = ['Injection Surgery', 'Protein Expression Check', 'Baseplating',  'Handling', 'Scoring', 'Food Scheduling fixed amount', 'Food Scheduling fixed time', 'Water Scheduling', 'Non Scheduling Experiment', 'Euthanasia']
#Procedures_names = ['Surgery', 'Protein Expression Check', 'Baseplating',  'Handling', 'Scoring', 'Food Scheduling fixed amount', 'Food Scheduling fixed time', 'Water Scheduling', 'Non Scheduling Experiment', 'Euthanasia']


Functions = {}
Steps_names = {}
for procedure in Procedures_names:
    # Vadim
    # function_name = minimize(procedure)
    function_name = '_'+minimize(procedure)
    Functions[procedure] = locals()[function_name]


for procedure in Procedures_names:
    steps_list_name = minimize(procedure)+'_steps'
    Steps_names[procedure] = locals()[steps_list_name]



def set_reference_weight_to_false(mouse_id):
    actions = db.session.query(Steps.id).filter(Steps.mouse_id==mouse_id).subquery()
    weight_entry = db.session.query(Entries).filter(Entries.step_id.in_(actions),  Entries.reference_weight).order_by(desc(Entries.id)).first() 
    if weight_entry:
        if weight_entry.content:
            weight_entry.reference_weight = False
            db.session.commit()
            # weight = float(weight_entry.content)
            # return jsonify({"lastweight":weight})
        # else:
            # db.session.delete(weight_entry)
            # db.session.commit()
            # return get_last_weight(mouse_id)
    # else:
        # return jsonify({"lastweight":None})



@bp.route('/<int:id>/start_experiment', methods=('GET', 'POST')) #/<int:id>/<experiment>/
@login_required
def start_experiment(id):
    mouse = get_mouse(id)
    def get_template(action):
        template_name = ""
        for a in action.lower().split(" "):
            template_name += a + "_"
        template_name = template_name[:-1]
        return(template_name)   

    experiment = mouse.experiment
    last_procedure = db.session.query(Procedures).filter(Procedures.mouse_id==id, ~Procedures.finished).order_by(desc(Procedures.id)).first()
    if last_procedure:
        template_name = get_template(last_procedure.name)
        step = Steps.query.filter(Steps.mouse_id==id, Steps.procedure_id==last_procedure.id).order_by(desc(Steps.id)).first()
        if not step:
            step_args = {'name': Steps_names[last_procedure.name][0], 'mouse_id':id, 'procedure_id':last_procedure.id, 'user_id':session['user_id']}
            step = Steps(**step_args)
            db.session.add(step)
            db.session.commit()
        return redirect(url_for('experiments.'+template_name, id=mouse.id, step_id=step.id)) 
    experiment_actions = db.session.query(Experiment_actions.name).filter(Experiment_actions.experiment_id==experiment).subquery()
    last_procedure = db.session.query(Procedures).filter(Procedures.mouse_id==id,  Procedures.name.in_(experiment_actions)).order_by(desc(Procedures.id)).first()      
    if not last_procedure:
        procedure = next_procedure(id)
        # set "refrence_weight" to "false" in db "entries"
        # set_reference_weight_to_false(mouse.id)
    # SOMETHING WRONG HERE BECAUSE CASE "else" is considered about in "if last_procedure"
    else:
        procedure = next_procedure(id, last_procedure.name)
        set_reference_weight_to_false(mouse.id)
    if procedure=='dead':
        procedure = Steps.query.filter(Steps.name == 'Euthanasia', Steps.mouse_id == id).order_by(desc(Steps.id)).first()
        euthanasia_time = Entries.query.filter(Entries.step_id==procedure.id, Entries.name=="Euthanasia time").first()
        euthanasia_time = datetime.strptime(euthanasia_time.content, "%Y-%m-%dT%H:%M")
        euthanasia_time = euthanasia_time.strftime("%A, %d. %B %Y %I:%M%p")
        flash('Mouse '+mouse.irats_id+' was euthanized on '+ euthanasia_time)
        return redirect(url_for('mouse.index'))
    
    return render_template('actions/choice.html', procedures=procedure, mouse=mouse, all_procedures=Procedures_names)


@bp.route('/<int:id>/select_next_procedure/<procedure_name>', methods=('GET', 'POST'))
@login_required
def select_next_procedure(id, procedure_name):
    procedure = Procedures(procedure_name, id, False)
    db.session.add(procedure)
    db.session.commit()

    return redirect(url_for('experiments.start_experiment', id=id))

@bp.route('/<int:id>/design_experiment', methods=('GET', 'POST'))
@login_required
def design_experiment(id):
    mouse_id = id
    user_id = session.get('user_id')
    
    if request.method == 'POST':
    
        forms = request.form.to_dict(flat=True)
        project = Projects.query.filter(Projects.name==forms.pop('project'), Projects.user_id==user_id).order_by(desc(Projects.id)).first()
        experiment = {'name':forms.pop('name'), 'user_id':user_id, 'project_id':project.id}
        experiment = Experiments(**experiment)
        db.session.add(experiment)
        db.session.commit()
        action_arg = {'experiment_id':experiment.id}
        euthanasia = False
        max_index = 0
        for id in forms:
            action_arg['name'] = forms[id]
            index = int(id.split("_")[-1])-1
            action_arg['index'] = index
            if index > max_index:
                max_index = index
            if forms[id].lower() == 'euthanasia':
                action_arg['final'] = True
                euthanasia = True
            else:
                action_arg['final'] = False
            db.session.add(Experiment_actions(**action_arg))
            db.session.commit()
        if not euthanasia:
            action_arg['name'] = "Euthanasia"
            action_arg['index'] = max_index + 1
            action_arg['final'] = True
            db.session.add(Experiment_actions(**action_arg))
            db.session.commit()
        

        return redirect(url_for('experiments.choose_experiment', id=mouse_id))

    user_projects = Projects.query.filter(Projects.user_id==user_id).all()

    
    return render_template('actions/experiment_design.html', id=id, actions=Procedures_names, projects=user_projects)