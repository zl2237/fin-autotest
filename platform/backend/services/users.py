from __future__ import annotations

from typing import List, Optional

from services.db import db


class UserService:
    def list(self) -> List[dict]:
        with db._cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, name, phone, email, role, created_at, updated_at FROM users ORDER BY user_id"
            )
            rows = cursor.fetchall()
            return [
                {
                    "user_id": row["user_id"],
                    "username": row["username"],
                    "name": row["name"],
                    "phone": row["phone"],
                    "email": row["email"],
                    "role": row["role"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

    def get_by_phone(self, phone: str) -> Optional[dict]:
        with db._cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, name, phone, email, password, role, created_at, updated_at FROM users WHERE phone = ?",
                (phone,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "name": row["name"],
                "phone": row["phone"],
                "email": row["email"],
                "password": row["password"],
                "role": row["role"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def get(self, username: str) -> Optional[dict]:
        with db._cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, name, phone, email, password, role, created_at, updated_at FROM users WHERE username = ?",
                (username,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "name": row["name"],
                "phone": row["phone"],
                "email": row["email"],
                "password": row["password"],
                "role": row["role"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def get_by_user_id(self, user_id: int) -> Optional[dict]:
        with db._cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, name, phone, email, password, role, created_at, updated_at FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "name": row["name"],
                "phone": row["phone"],
                "email": row["email"],
                "password": row["password"],
                "role": row["role"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def create(self, username: str, password: str, role: str, name: str, phone: str, email: str) -> dict:
        with db._cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, role, name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                (username, password, role, name, phone, email),
            )
            user_id = cursor.lastrowid
        return self.get_by_user_id(user_id)

    def update(
        self,
        user_id: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        fields = []
        values = []
        if username is not None:
            fields.append("username = ?")
            values.append(username)
        if password is not None:
            fields.append("password = ?")
            values.append(password)
        if role is not None:
            fields.append("role = ?")
            values.append(role)
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if not fields:
            return self.get_by_user_id(user_id)
        values.append(user_id)
        with db._cursor() as cursor:
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", values)
        return self.get_by_user_id(user_id)

    def delete(self, username: str) -> None:
        with db._cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))

    def is_phone_taken(self, phone: str, exclude_user_id: Optional[int] = None) -> bool:
        with db._cursor() as cursor:
            if exclude_user_id is None:
                cursor.execute("SELECT 1 FROM users WHERE phone = ?", (phone,))
            else:
                cursor.execute("SELECT 1 FROM users WHERE phone = ? AND user_id <> ?", (phone, exclude_user_id))
            return cursor.fetchone() is not None


user_service = UserService()
