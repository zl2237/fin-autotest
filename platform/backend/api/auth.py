from flask import Blueprint, jsonify, request

from services.auth import validate, make_token, get_role
from services.users import user_service

bp = Blueprint("auth", __name__)


@bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    ok, error = validate(phone, password)
    if not ok:
        return jsonify({"ok": False, "message": error}), 401
    token = make_token(phone)
    role = get_role(phone)
    user = user_service.get_by_phone(phone)
    return jsonify({
        "ok": True,
        "token": token,
        "username": user["username"] if user else phone,
        "role": role,
        "name": user["name"] if user else "",
        "phone": user["phone"] if user else phone,
        "email": user["email"] if user else "",
        "user_id": user["user_id"] if user else None,
    })


@bp.route("/api/auth/me", methods=["GET", "PUT"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return jsonify({"ok": False, "message": "未登录"}), 401
    try:
        token_part = auth_header.split(".", 1)[0]
        identifier = token_part.split(":", 1)[0]
    except Exception:
        return jsonify({"ok": False, "message": "Token 无效"}), 401
    user = user_service.get(identifier) or user_service.get_by_phone(identifier)
    if not user:
        return jsonify({"ok": False, "message": "用户不存在"}), 404
    if request.method == "GET":
        return jsonify({
            "ok": True,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "name": user["name"],
                "phone": user["phone"],
                "email": user["email"],
                "role": user["role"],
            },
        })
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    password = data.get("password")
    if name is not None and not str(name).strip():
        return jsonify({"ok": False, "message": "姓名不能为空"}), 400
    if phone is not None and not str(phone).strip():
        return jsonify({"ok": False, "message": "手机号不能为空"}), 400
    if phone is not None and user_service.is_phone_taken(str(phone).strip(), exclude_user_id=user["user_id"]):
        return jsonify({"ok": False, "message": "手机号已存在"}), 400
    patch: dict = {}
    if name is not None:
        patch["name"] = str(name).strip()
    if phone is not None:
        patch["phone"] = str(phone).strip()
    if email is not None:
        patch["email"] = str(email).strip()
    if password is not None and str(password).strip():
        patch["password"] = str(password).strip()
    if not patch:
        return jsonify({"ok": True})
    updated = user_service.update(user["user_id"], **patch)
    return jsonify({
        "ok": True,
        "user": {
            "user_id": updated["user_id"],
            "username": updated["username"],
            "name": updated["name"],
            "phone": updated["phone"],
            "email": updated["email"],
            "role": updated["role"],
        },
    })


@bp.route("/api/auth/check-phone", methods=["GET"])
def check_phone():
    phone = (request.args.get("phone") or "").strip()
    exclude_user_id = request.args.get("exclude_user_id")
    if not phone:
        return jsonify({"ok": False, "message": "手机号不能为空"}), 400
    taken = user_service.is_phone_taken(
        phone,
        exclude_user_id=int(exclude_user_id) if exclude_user_id and str(exclude_user_id).isdigit() else None,
    )
    return jsonify({"ok": True, "taken": taken})
