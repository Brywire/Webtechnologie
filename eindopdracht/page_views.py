from datetime import date

from flask import render_template, request
from flask_login import current_user, login_required

from models import Task


@login_required
def index():
    filter_param = request.args.get("filter", "all")
    today = date.today()

    query = Task.query.filter_by(user_id=current_user.id)

    if filter_param == "open":
        query = query.filter_by(done=False)
    elif filter_param == "done":
        query = query.filter_by(done=True)
    elif filter_param == "urgent":
        query = query.filter(
            Task.done.is_(False),
            Task.deadline.isnot(None),
            Task.deadline <= date.fromordinal(today.toordinal() + 3),
        )

    tasks = query.order_by(Task.deadline.asc().nullslast(), Task.created_at.desc()).all()
    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    stats = {
        "total": len(all_tasks),
        "done": sum(1 for task in all_tasks if task.done),
        "open": sum(1 for task in all_tasks if not task.done),
    }

    return render_template("index.html", tasks=tasks, today=today, filter=filter_param, stats=stats)


@login_required
def profile():
    total = len(current_user.tasks)
    done = sum(1 for task in current_user.tasks if task.done)
    open_ = total - done
    return render_template("profile.html", total=total, done=done, open_=open_)
