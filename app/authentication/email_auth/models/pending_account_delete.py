from uuid import UUID

from pydantic import BaseModel


class PendingAccountDeleteRequest(BaseModel):
    user_id: UUID
