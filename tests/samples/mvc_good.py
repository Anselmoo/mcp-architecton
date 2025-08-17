def render(data: str) -> str:
    return f"view:{data}"


class UserModel:
    def get_user(self, user_id: int) -> str:
        return f"user-{user_id}"


class UserController:
    def show(self, user_id: int) -> str:
        m = UserModel()
        data = m.get_user(user_id)
        return render(data)
