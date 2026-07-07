import os
import secrets
from typing import Optional

from services.db import db


def get_user(identifier: str) -> Optional[dict]:
    with db._cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, password, role, name, phone, email FROM users WHERE username = ? OR phone = ?",
            (identifier, identifier),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "password": row["password"],
            "role": row["role"],
            "name": row["name"],
            "phone": row["phone"],
            "email": row["email"],
        }


def validate(phone: str, password: str) -> tuple[bool, Optional[str]]:
    user = get_user(phone)
    if not user:
        return False, "手机号未注册"
    if user["password"] != password:
        return False, "密码错误"
    return True, None


def get_role(identifier: str) -> str:
    user = get_user(identifier)
    if not user:
        return "user"
    return user["role"]


def make_token(identifier: str) -> str:
    role = get_role(identifier)
    payload = f"{identifier}:{role}.{secrets.token_hex(16)}"
    return payload
