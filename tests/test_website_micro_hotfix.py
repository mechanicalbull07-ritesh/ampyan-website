"""Canonical navigation and RFC 6068 drafts; no OS mail client or production calls."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import pytest
from .test_canonical_garage import backend, client, csrf, snapshot
from .test_account_deletion_discovery import Document


def mail_fields(uri):
    target=urlsplit(uri)
    # mailto percent-decoding intentionally does NOT translate literal '+' to spaces.
    fields={unquote(k):unquote(v) for k,v in (part.split('=',1) for part in target.query.split('&'))}
    return target,fields


def test_mailto_rfc6068_spaces_crlf_and_safe_static_content(monkeypatch):
    import app as website
    from services import manual_deletion as mail
    with website.app.test_request_context():
        uri=mail.context()['deletion_mailto'];target,fields=mail_fields(uri)
    assert target.scheme=='mailto' and unquote(target.path)=='hiampyan@gmail.com'
    assert fields['subject']=='AMPYAN Account Deletion Request'
    assert set(fields)=={'subject','body'}
    assert '+' not in target.query and '%20' in target.query and '%0D%0A' in target.query
    assert fields['body']==mail.BODY and '\r\n\r\n' in fields['body'] and ' ' in fields['body']
    assert all(word not in fields['body'] for word in ['user_id','password','bearer','OTP','credential','receipt','@'])
    assert '\r' not in fields['subject'] and '\n' not in fields['subject']


def test_mailto_configured_recipient_reserved_characters_and_literal_plus(monkeypatch):
    import app as website
    from services import manual_deletion as mail
    monkeypatch.setitem(website.app.config,'AMPYAN_SUPPORT_EMAIL','support+delete#tag@example.invalid')
    monkeypatch.setattr(mail,'SUBJECT','A+B & café')
    monkeypatch.setattr(mail,'BODY','First line with spaces\r\nSecond + line')
    with website.app.test_request_context():
        uri=mail.context()['deletion_mailto'];target,fields=mail_fields(uri)
    assert unquote(target.path)=='support+delete#tag@example.invalid' and target.fragment==''
    assert fields=={'subject':'A+B & café','body':'First line with spaces\r\nSecond + line'}
    assert '%2B' in target.query and '+' not in target.query


def test_rendered_deletion_cta_uses_rfc_uri_and_discovery_preserved():
    import app as website
    from models.models import db
    with website.app.app_context():
        db.create_all();c=website.app.test_client();page=c.get('/account-deletion')
        doc=Document(page.data);links=[n for n in doc.nodes if n.tag=='a' and n.attrs.get('href','').startswith('mailto:')]
        assert len(links)==1
        target,fields=mail_fields(links[0]['href'])
        assert unquote(target.path)=='hiampyan@gmail.com' and fields['subject']=='AMPYAN Account Deletion Request'
        assert '+' not in target.query and '\r\n' in fields['body']
        assert doc.select_one('footer a[href="/account-deletion"]')
        assert c.post('/api/help-report',json={'category':'Account Deletion'}).status_code==303


def test_one_unambiguous_canonical_health_route():
    import app as website
    rules=[r for r in website.app.url_map.iter_rules() if r.rule=='/my-car-health' and 'GET' in r.methods]
    assert len(rules)==1 and rules[0].endpoint=='garage.garage_dashboard'
    assert website.app.test_client().get('/mygarage').location.endswith('/my-car-health')


def test_profile_health_navigation_is_website_get_and_app_handoff_remains(client, backend):
    profile=client.get('/profile');assert profile.status_code==200
    doc=Document(profile.data)
    health=doc.select_one('.profile-actions a[href="/my-car-health"]')
    assert health and health.get_text(strip=True)=='My Car Health'
    nav=[n for n in doc.nodes if n.tag=='a' and n.get_text(' ',strip=True)=='My Car Health']
    assert nav and all(n['href']=='/my-car-health' for n in nav)
    manage=[n for n in doc.nodes if n.tag=='a' and n.get_text(' ',strip=True)=='Manage vehicles in App']
    assert manage and all(n['href']=='https://play.google.com/store/apps/details?id=com.ampyan.app' for n in manage)
    before=snapshot(backend);response=client.get(health['href']);after=snapshot(backend)
    assert response.status_code==200 and not response.location and b'My Car Health' in response.data
    assert before==after
    health_doc=Document(response.data)
    forms=health_doc.select('main form')
    assert forms and all(n.attrs.get('method','get').lower()=='get' for n in forms)
    assert not health_doc.select('main input') and not health_doc.select('main textarea')
    assert all(n.attrs.get('name')=='car_id' for n in health_doc.select('main select'))


def test_all_template_my_car_health_links_use_canonical_website_route():
    root=Path(__file__).resolve().parents[1]/'templates';seen=0
    for path in root.rglob('*.html'):
        doc=Document(path.read_text())
        for n in doc.nodes:
            label=n.get_text(' ',strip=True)
            # Conditional anchors are checked in the rendered authenticated Profile.
            if n.tag=='a' and '{%' not in label and 'my car health' in label.lower():
                assert urlsplit(n.attrs['href']).path=='/my-car-health',str(path)
                seen+=1
    assert seen>=5
