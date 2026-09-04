from stockmon.api.schemas.base import CamelModel
from stockmon.db.models import User as UserRow


class LoginRequest(CamelModel):
    username: str
    password: str


class UserSchema(CamelModel):
    id: int
    username: str
    email: str | None

    @classmethod
    def from_row(cls, row: UserRow) -> "UserSchema":
        return cls(id=row.id, username=row.username, email=row.email)
