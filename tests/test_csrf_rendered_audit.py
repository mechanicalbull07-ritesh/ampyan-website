"""Render each previously disputed form and exercise the real CSRF middleware."""
from html.parser import HTMLParser
from flask import render_template, session
from flask.testing import FlaskClient
from flask_wtf.csrf import validate_csrf
import pytest
import app as website

class Forms(HTMLParser):
    def __init__(self):
        super().__init__(); self.forms=[]; self.current=None
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='form': self.current={'attrs':attrs,'inputs':[]}
        elif tag=='input' and self.current is not None: self.current['inputs'].append(attrs)
    def handle_endtag(self, tag):
        if tag=='form' and self.current is not None:
            self.forms.append(self.current); self.current=None

CASES=[('connect','/garage/connect',1),('garage','/garage',2),('add','/add-car',1),
       ('edit','/edit-car/201',4),('services','/garage/cars/201/services',1),
       ('confirmation','/verify-email/synthetic',1)]

@pytest.mark.parametrize('view,path,count',CASES)
def test_ten_rendered_forms_and_middleware(monkeypatch,view,path,count):
    car={'id':201,'brand':'Synthetic','model':'Audit','transmission':'UNKNOWN'}
    with website.app.test_request_context(path):
        html=render_template('confirm_email.html' if view=='confirmation' else 'canonical_garage.html',
            view=view,car=car,cars=[car],mileage={},history={},records=[],symptoms={},transmissions=['UNKNOWN'],
            operation_id='synthetic',observed_at='2026-10-02',service_types=['General service'])
        parser=Forms();parser.feed(html)
        forms=[f for f in parser.forms if f['attrs'].get('method','get').lower()=='post']
        assert len(forms)==count
        cookie_state=dict(session)
        for form in forms:
            fields=[i for i in form['inputs'] if i.get('name')=='csrf_token']
            assert len(fields)==1 and fields[0].get('type')=='hidden' and 'disabled' not in fields[0]
            validate_csrf(fields[0]['value'])
    for form in forms:
        target=form['attrs'].get('action') or path
        endpoint,_=website.app.url_map.bind('localhost').match(target,method='POST')
        assert endpoint not in website.csrf._exempt_blueprints
        # Isolate middleware from destructive/business handlers, keeping real routing and before_request checks.
        monkeypatch.setitem(website.app.view_functions,endpoint,lambda **kwargs: ('csrf middleware passed',204))
        client=FlaskClient(website.app,website.app.response_class)
        with client.session_transaction() as saved: saved.update(cookie_state)
        assert client.post(target).status_code==400
        assert client.post(target,data={'csrf_token':'invalid'}).status_code==400
        value=next(i['value'] for i in form['inputs'] if i.get('name')=='csrf_token')
        assert client.post(target,data={'csrf_token':value}).status_code==204
