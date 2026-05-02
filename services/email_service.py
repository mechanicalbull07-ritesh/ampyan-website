from flask_mail import Message
import os

def send_email(mail, to, subject, body):

    try:

        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            sender=("Motrnoix AMPYAN", os.environ.get("MAIL_FROM"))
        )

        mail.send(msg)

        print("EMAIL SENT SUCCESSFULLY")

    except Exception as e:

        print("EMAIL ERROR:", e)
