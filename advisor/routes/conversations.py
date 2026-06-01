from django.utils import timezone
from fastapi import APIRouter, HTTPException

from advisor.models import Conversation, Message
from advisor.schemas import MessageRequest, TitleRequest

router = APIRouter(prefix="/convs", tags=["Conversations"])


@router.get("/")
def list_convs():
    """List all conversations ordered by most recently updated."""
    return [
        {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in Conversation.objects.all()
    ]


@router.post("/")
def create_conv():
    """Create a new conversation and return its id and title."""
    conv = Conversation.objects.create()
    return {"id": conv.id, "title": conv.title}


@router.delete("/{conv_id}")
def delete_conv(conv_id: int):
    """Delete a conversation and all its messages."""
    deleted, _ = Conversation.objects.filter(pk=conv_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@router.patch("/{conv_id}/title")
def rename_conv(conv_id: int, body: TitleRequest):
    """Set the title of a conversation."""
    updated = Conversation.objects.filter(pk=conv_id).update(title=body.title[:120])
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@router.get("/{conv_id}/messages/")
def get_messages(conv_id: int):
    """Return all messages for a conversation as a history array."""
    if not Conversation.objects.filter(pk=conv_id).exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [
        {"role": m.role, "content": m.content}
        for m in Message.objects.filter(conversation_id=conv_id)
    ]


@router.post("/{conv_id}/messages/")
def append_message(conv_id: int, body: MessageRequest):
    """Append a message to a conversation and touch its updated_at timestamp."""
    try:
        conv = Conversation.objects.get(pk=conv_id)
    except Conversation.DoesNotExist:
        raise HTTPException(status_code=404, detail="Conversation not found")
    Message.objects.create(conversation=conv, role=body.role, content=body.content)
    conv.updated_at = timezone.now()
    conv.save(update_fields=["updated_at"])
    return {"status": "ok"}
