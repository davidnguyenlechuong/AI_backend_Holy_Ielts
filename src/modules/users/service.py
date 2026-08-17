from src.models.auth import User


def user_to_me_dict(user: User) -> dict:
    return {"id": str(user.id), "name": user.name, "email": user.email}
