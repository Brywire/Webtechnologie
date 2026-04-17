from datetime import date, datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Task


@login_required
def add_task():
    today = date.today()

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
        db.session.commit()

        flash(f'Taak "{title}" toegevoegd!', "success")
        return redirect(url_for("index"))

    return render_template("add_task.html", today=today)


@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash("Je hebt geen toegang tot deze taak.", "error")
        return redirect(url_for("index"))

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

        task.title = title
        task.description = description
        task.subject = subject
        task.priority = priority
        task.deadline = deadline
        db.session.commit()

        flash(f'Taak "{title}" bijgewerkt!', "success")
        return redirect(url_for("index"))

    return render_template("edit_task.html", task=task)


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
