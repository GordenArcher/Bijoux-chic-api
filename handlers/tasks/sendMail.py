from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from celery import shared_task


@shared_task
def send_email(user, htmltemplate, subject):
    html_content = render_to_string(htmltemplate or "Emails/welcome.html", {
        "user": f"{user.get_full_name()}" 
    })

    email = EmailMessage(
        subject=subject or "Thanks for Joining Bijoux Chic",
        body=html_content,
        from_email="Bijoux Chic Shop <no-reply@bijouxcgic.com>",
        to=[user.email],
    )

    email.content_subtype = "html"
    email.send()

