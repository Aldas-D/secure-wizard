"""Administravimo srities prieigos kontrolė."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import redirect, request, session, url_for

F = TypeVar("F", bound=Callable[..., Any])


def admin_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return cast(F, wrapped)


def is_admin() -> bool:
    return bool(session.get("admin_authenticated"))
