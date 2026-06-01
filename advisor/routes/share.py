from django.conf import settings as django_settings
from django.core.mail import EmailMessage
from fastapi import APIRouter
from fastapi.responses import Response

from advisor.html_export import wrap_html_for_export
from advisor.schemas import ShareRequest

router = APIRouter(tags=["AI"])


@router.post("/share/email")
def share_email(body: ShareRequest):
    """Email an advisor response to the owner."""
    from networth.models import User
    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not owner:
        return {"status": "error", "message": "No owner account found."}

    html = wrap_html_for_export(body.content_html, body.title)
    msg = EmailMessage(
        subject=f"Advisor Note — {body.title}",
        body=html,
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        to=[owner.email],
    )
    msg.content_subtype = "html"
    msg.send()
    return {"status": "success", "message": f"Sent to {owner.email}"}


@router.post("/share/pdf")
def share_pdf(body: ShareRequest):
    """Return an advisor response as a downloadable PDF."""
    from weasyprint import HTML
    html = wrap_html_for_export(body.content_html, body.title)
    pdf_bytes = HTML(string=html, base_url="").write_pdf()
    safe = body.title.encode("ascii", "ignore").decode("ascii")
    filename = (safe.replace(" ", "_").strip("_")[:40] or "advisor_note") + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
