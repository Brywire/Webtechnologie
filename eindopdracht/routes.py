import auth_views
import page_views
import task_views


ROUTES = [
    ("/", "index", page_views.index, ["GET"]),
    ("/register", "register", auth_views.register, ["GET", "POST"]),
    ("/login", "login", auth_views.login, ["GET", "POST"]),
    ("/logout", "logout", auth_views.logout, ["GET"]),
    ("/profile", "profile", page_views.profile, ["GET"]),
    ("/add", "add_task", task_views.add_task, ["GET", "POST"]),
    ("/task/<int:task_id>/edit", "edit_task", task_views.edit_task, ["GET", "POST"]),
    ("/task/<int:task_id>/toggle", "toggle_task", task_views.toggle_task, ["POST"]),
    ("/task/<int:task_id>/delete", "delete_task", task_views.delete_task, ["POST"]),
]


def register_routes(app):
    for url, endpoint, view_func, methods in ROUTES:
        app.add_url_rule(url, endpoint=endpoint, view_func=view_func, methods=methods)
