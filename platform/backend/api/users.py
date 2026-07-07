from typing import Optional

from flask import Blueprint, jsonify, request

from services.auth import get_role
from services.users import user_service

bp = Blueprint("users", __name__)


def _require_admin() -> Optional[dict]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    try:
        token_part = auth_header.split(".", 1)[0]
        identifier = token_part.split(":", 1)[0]
        role = get_role(identifier)
    except Exception:
        return None
    if role != "admin":
        return None
    operator = user_service.get(identifier) or user_service.get_by_phone(identifier)
    if not operator:
        return None
    return {"user_id": operator["user_id"], "username": operator["username"], "role": operator["role"]}


@bp.route("/api/users", methods=["GET"])
def list_users():
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    users = user_service.list()
    return jsonify({"ok": True, "users": users})


@bp.route("/api/users", methods=["POST"])
def create_user():
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "user").strip()
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    if not username or not password:
        return jsonify({"ok": False, "message": "账号和密码不能为空"}), 400
    if role not in {"admin", "user"}:
        return jsonify({"ok": False, "message": "角色无效"}), 400
    if not phone:
        return jsonify({"ok": False, "message": "手机号不能为空"}), 400
    if user_service.is_phone_taken(phone):
        return jsonify({"ok": False, "message": "手机号已存在"}), 400
    try:
        user = user_service.create(username, password, role, name, phone, email)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True, "user": {
        "user_id": user["user_id"],
        "username": user["username"],
        "name": user["name"],
        "phone": user["phone"],
        "email": user["email"],
        "role": user["role"],
    }})


@bp.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    if operator["user_id"] == user_id:
        return jsonify({"ok": False, "message": "不支持修改当前账号"}), 400
    user = user_service.get_by_user_id(user_id)
    if not user:
        return jsonify({"ok": False, "message": "用户不存在"}), 404
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    if role is not None and role not in {"admin", "user"}:
        return jsonify({"ok": False, "message": "角色无效"}), 400
    if username is not None and not str(username).strip():
        return jsonify({"ok": False, "message": "账号不能为空"}), 400
    if name is not None and not str(name).strip():
        return jsonify({"ok": False, "message": "姓名不能为空"}), 400
    if phone is not None and not str(phone).strip():
        return jsonify({"ok": False, "message": "手机号不能为空"}), 400
    if phone is not None and user_service.is_phone_taken(str(phone).strip(), exclude_user_id=user_id):
        return jsonify({"ok": False, "message": "手机号已存在"}), 400
    try:
        updated = user_service.update(
            user_id,
            username=str(username).strip() if username is not None else None,
            password=str(password).strip() if password is not None else None,
            role=role,
            name=str(name).strip() if name is not None else None,
            phone=str(phone).strip() if phone is not None else None,
            email=str(email).strip() if email is not None else None,
        )
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True, "user": {
        "user_id": updated["user_id"],
        "username": updated["username"],
        "name": updated["name"],
        "phone": updated["phone"],
        "email": updated["email"],
        "role": updated["role"],
    }})


@bp.route("/api/users/<username>", methods=["DELETE"])
def delete_user(username: str):
    operator = _require_admin()
    if not operator:
        return jsonify({"ok": False, "message": "无权限"}), 403
    user = user_service.get(username)
    if not user:
        return jsonify({"ok": False, "message": "用户不存在"}), 404
    if operator["user_id"] == user["user_id"]:
        return jsonify({"ok": False, "message": "不支持删除当前账号"}), 400
    try:
        user_service.delete(username)
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    return jsonify({"ok": True})
