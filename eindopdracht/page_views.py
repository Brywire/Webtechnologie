from datetime import date

from flask import jsonify, render_template, request
from flask_login import current_user, login_required

from models import Task
from task_ordering import topological_sort_tasks


@login_required
def index():
    filter_param = request.args.get("filter", "all")
    sort_param = request.args.get("sort", "deadline")
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
    tasks_topo, topo_has_cycle = topological_sort_tasks(tasks)
    if sort_param == "topological":
        tasks = tasks_topo

    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    stats = {
        "total": len(all_tasks),
        "done": sum(1 for task in all_tasks if task.done),
        "open": sum(1 for task in all_tasks if not task.done),
    }

    return render_template(
        "index.html",
        tasks=tasks,
        tasks_topo_order=tasks_topo,
        topo_has_cycle=topo_has_cycle,
        today=today,
        filter=filter_param,
        sort=sort_param,
        stats=stats,
    )


@login_required
def tasks_topological_order_json():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    ordered, has_cycle = topological_sort_tasks(tasks)
    return jsonify(
        {
            "order": [{"id": t.id, "title": t.title, "done": t.done} for t in ordered],
            "has_cycle": has_cycle,
        }
    )


@login_required
def profile():
    total = len(current_user.tasks)
    done = sum(1 for task in current_user.tasks if task.done)
    open_ = total - done
    return render_template("profile.html", total=total, done=done, open_=open_)
