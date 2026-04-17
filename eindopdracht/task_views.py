from datetime import date, datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Task
from task_ordering import prerequisite_set_creates_cycle


def _parse_prerequisite_ids(req):
    out = []
    for x in req.form.getlist("prerequisite_ids"):
        try:
            out.append(int(x))
        except ValueError:
            continue
    return out


def _tasks_for_prerequisite_picker(exclude_task_id=None):
    q = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc())
    if exclude_task_id is not None:
        q = q.filter(Task.id != exclude_task_id)
    return q.all()


@login_required
def add_task():
    today = date.today()
    other_tasks = _tasks_for_prerequisite_picker()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        subject = request.form.get("subject", "").strip()
        priority = request.form.get("priority", "medium")
        deadline_str = request.form.get("deadline", "")

        if not title:
            flash("Een taaknaam is verplicht.", "error")
            return redirect(url_for("add_task"))

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Ongeldige deadline datum.", "error")
                return redirect(url_for("add_task"))

        new_task = Task(
            title=title,
            description=description,
            subject=subject,
            priority=priority,
            deadline=deadline,
            user_id=current_user.id,
        )
        db.session.add(new_task)
        db.session.flush()

        wanted = set(_parse_prerequisite_ids(request))
        wanted.discard(new_task.id)
        valid = Task.query.filter(
            Task.user_id == current_user.id,
            Task.id.in_(wanted),
        ).all()
        new_task.prerequisites = valid
        db.session.commit()

        flash(f'Taak "{title}" toegevoegd!', "success")
        return redirect(url_for("index"))

    return render_template("add_task.html", today=today, other_tasks=other_tasks)


@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Je hebt geen toegang tot deze taak.", "error")
        return redirect(url_for("index"))

    other_tasks = _tasks_for_prerequisite_picker(exclude_task_id=task_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        subject = request.form.get("subject", "").strip()
        priority = request.form.get("priority", "medium")
        deadline_str = request.form.get("deadline", "")

        if not title:
            flash("Een taaknaam is verplicht.", "error")
            return redirect(url_for("edit_task", task_id=task_id))

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Ongeldige deadline datum.", "error")
                return redirect(url_for("edit_task", task_id=task_id))

        wanted = set(_parse_prerequisite_ids(request))
        wanted.discard(task_id)
        valid = Task.query.filter(
            Task.user_id == current_user.id,
            Task.id.in_(wanted),
        ).all()
        new_prereq_ids = {t.id for t in valid}
        all_tasks = Task.query.filter_by(user_id=current_user.id).all()
        if prerequisite_set_creates_cycle(all_tasks, task, new_prereq_ids):
            flash("Deze afhankelijkheden vormen een cyclus. Pas ze aan.", "error")
            return redirect(url_for("edit_task", task_id=task_id))

        task.title = title
        task.description = description
        task.subject = subject
        task.priority = priority
        task.deadline = deadline
        task.prerequisites = valid
        db.session.commit()

        flash(f'Taak "{title}" bijgewerkt!', "success")
        return redirect(url_for("index"))

    selected_prereq_ids = {p.id for p in task.prerequisites}
    return render_template(
        "edit_task.html",
        task=task,
        other_tasks=other_tasks,
        selected_prereq_ids=selected_prereq_ids,
    )


@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Je hebt geen toegang tot deze taak.", "error")
        return redirect(url_for("index"))

    task.done = not task.done
    db.session.commit()
    return redirect(url_for("index"))


@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Je hebt geen toegang tot deze taak.", "error")
        return redirect(url_for("index"))

    db.session.delete(task)
    db.session.commit()
    flash("Taak verwijderd.", "success")
    return redirect(url_for("index"))
