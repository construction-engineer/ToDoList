from pydantic import BaseModel
from typing import Union


class Chat(BaseModel):
    id: int
    username: Union[str, None]


class Message(BaseModel):
    chat: Chat
    text: Union[str, None] = None


class UpdateObj(BaseModel):
    update_id: int
    message: Message


class GetUpdatesResponse(BaseModel):
    ok: bool
    result: list[UpdateObj]


class SendMessageResponse (BaseModel):
    ok: bool
    result: Message
