from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


class ShareRequest(BaseModel):
    content_html: str
    title: str = "Financial Advisor Note"


class TitleRequest(BaseModel):
    title: str


class MessageRequest(BaseModel):
    role: str
    content: str
