"""Manual deletion UI contract; support address already published on AMPYAN Contact."""
import os
import re
from urllib.parse import urlencode
from flask import current_app

DEFAULT_SUPPORT_EMAIL = 'hiampyan@gmail.com'
SUBJECT = 'AMPYAN account deletion request'
BODY = ('Please delete my AMPYAN account and associated personal data. '
        'I am sending this request from the email registered with my AMPYAN account. '
        'I understand that deletion is permanent and ownership verification is required. '
        'Please advise on the processing steps and any applicable retention exceptions.')


def context():
    address = current_app.config.get('AMPYAN_SUPPORT_EMAIL', os.environ.get('AMPYAN_SUPPORT_EMAIL', DEFAULT_SUPPORT_EMAIL))
    if not isinstance(address, str) or not re.fullmatch(r'[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+', address):
        return {'support_email': None, 'deletion_mailto': None}
    return {'support_email': address, 'deletion_mailto': 'mailto:' + address + '?' + urlencode({'subject': SUBJECT, 'body': BODY})}
