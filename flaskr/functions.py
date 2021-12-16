from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from . import db, Mice
from sqlalchemy import desc
from sqlalchemy import engine




def index(table, road):
    mice = table.query.order_by(desc(table.id))
    return render_template(road, mice=mice)
