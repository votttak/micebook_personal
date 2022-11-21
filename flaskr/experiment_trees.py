
sample_exp = [['Injection Surgery', 'Implantation Surgery'], 'Protein Expression Check', 'Baseplating', 'Food scheduling', 'Euthanasia']
from .tables import Experiments, Experiment_actions, Mice, Procedures, Steps
from sqlalchemy import desc

print("---------------IN EXPERIMENT_TREES---------------")

def next_step(procedure, steps):
    last_step = Steps.query.filter(Steps.procedure_id == procedure.id).order_by(desc(Steps.id)).first()
    if not last_step:
        return steps[0]
    elif last_step in steps:
        index = steps.index(last_step)
        if index>=len(steps)-1:
            return steps[-1]
        else:
            return steps[index+1]
    else:
        return steps[0]
        # raise NameError('Wrong Step name. The requested step is not in this procedure')


def next_procedure(id, last_action=None):
    mouse = Mice.query.filter(Mice.id==id).first()
    experiment = mouse.experiment
    if not last_action:
        index = 0
    else:
        action = Experiment_actions.query.filter(Experiment_actions.experiment_id==experiment, Experiment_actions.name==last_action).first()
        if not action:
            return 'Injection Surgery'
            # raise NameError('Wrong Experiment or Action. The requested action is not in this experiment')
        index = action.index + 1

    next_actions = []
    actions = Experiment_actions.query.filter(Experiment_actions.experiment_id==experiment, Experiment_actions.index==index).all()

    if not actions:
        return 'dead'
    for action in actions:
        next_actions.append(action.name)

    return next_actions



def Severity(id, last_action=None):
    mouse = Mice.query.filter(Mice.id==id).first()
    experiment = mouse.experiment
    if not last_action:
        index = 0
    else:
        action = Experiment_actions.query.filter(Experiment_actions.experiment_id==experiment, Experiment_actions.name==last_action).first()
        if not action:
            return 'Injection Surgery'
            # raise NameError('Wrong Experiment or Action. The requested action is not in this experiment')
        index = action.index + 1

    next_actions = []
    actions = Experiment_actions.query.filter(Experiment_actions.experiment_id==experiment, Experiment_actions.index==index).all()
    print('actions', actions)
    if not actions:
        return 'dead'
    for action in actions:
        next_actions.append(action.name)

    return next_actions

def next_action_old(last_action=None, exp=sample_exp):
    flat_exp = []
    flat_indexes = []
    for i in range(len(exp)):
        if isinstance(exp[i], list):
            for j in range(len(exp[i])):
                flat_exp.append(exp[i][j])
                flat_indexes.append([i,j])
        else:
            flat_exp.append(exp[i])
            flat_indexes.append(i)

    if not last_action:
        return(sample_exp[0])
    elif last_action in flat_exp:
        if last_action == flat_exp[-1]:
            return 'dead'
        if last_action in exp:
            last_index = exp.index(last_action)
            return(exp[last_index+1])
        else:
            indexes = flat_indexes[flat_exp.index(last_action)]
            if indexes[1]==len(exp[indexes[0]])-1:
                return(exp[indexes[0]+1])
            else:
                return(exp[indexes[0]][indexes[1]+1])
    else:
        raise NameError('Wrong Experiment or Action. The requested action is not in this experiment')