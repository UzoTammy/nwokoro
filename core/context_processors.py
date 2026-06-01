from django.conf import settings


def ai_advisor_url(request):
    return {'AI_ADVISOR_URL': settings.AI_ADVISOR_URL}
