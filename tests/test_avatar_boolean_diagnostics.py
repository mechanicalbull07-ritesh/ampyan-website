"""Fixed stage/selection labels and booleans only; never log input values."""
import logging,subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
from flask import session
import app as website
from services import google_profile_picture as avatar
from tests.test_google_profile_picture import setup
BASE='d1e173a40f5507d8d6abe2d1ffc6e050ff5855c6'
PRIVATE='https://example.invalid/avatar?email=PRIVATE_EMAIL@example.invalid&token=PRIVATE_TOKEN&name=PRIVATE_NAME&cookie=PRIVATE_COOKIE'
SCHEMAS={
 'google_userinfo':{'google_userinfo_fallback_attempted'},
 'google_callback_exit':{'avatar_helper_called'},
 'google_callback':{'picture_claim_present','picture_value_nonempty','picture_url_accepted','avatar_helper_called','avatar_stored','google_userinfo_fallback_attempted'},
 'authenticated_request':{'avatar_session_present','avatar_user_binding_valid','uploaded_profile_photo_present','google_avatar_available','navbar_source'},
}
def records(caplog):return [r for r in caplog.records if r.getMessage().startswith('avatar_diagnostic ')]
def assert_private(caplog):
    result=records(caplog);assert result
    for r in result:
        fields=dict(part.split('=',1) for part in r.getMessage().split()[1:]);stage=fields.pop('stage')
        assert set(fields)==SCHEMAS[stage]
        for k,v in fields.items():assert v in ({'uploaded','google','fallback'} if k=='navbar_source' else {'True','False'})
        for v in r.args:assert type(v) is bool or v in ('uploaded','google','fallback')
        for secret in ('https://','@','PRIVATE_NAME','PRIVATE_COOKIE','PRIVATE_TOKEN','PRIVATE_EMAIL','PRIVATE_USER_ID','synthetic-id-only','synthetic-bearer-only'):
            assert secret not in r.getMessage()
    return result
@pytest.fixture
def old_helper():
    s=subprocess.check_output(['git','show',BASE+':services/google_profile_picture.py'],cwd=Path(__file__).resolve().parents[1],text=True)
    module={};exec(compile(s,'pre-diagnostics-avatar-helper','exec'),module);return module
@pytest.mark.parametrize('claims',[{}, {'picture':None},{'picture':''},{'picture':PRIVATE},{'picture':'http://example.invalid/avatar'},
    {'picture':'https://private:credential@example.invalid/avatar'},{'picture':'https://example.invalid/'+('x'*2049)},{'picture':'https://[invalid-host'}])
def test_callback_whitelist_and_identical_behavior(caplog,old_helper,claims):
    caplog.set_level(logging.INFO)
    with website.app.test_request_context():
        session[avatar.SESSION_KEY]={'website_user':'old','url':PRIVATE}
        old_helper['remember_google_picture']('PRIVATE_USER_ID',claims);expected=dict(session)
    with website.app.test_request_context():
        session[avatar.SESSION_KEY]={'website_user':'old','url':PRIVATE}
        avatar.remember_google_picture('PRIVATE_USER_ID',claims);assert dict(session)==expected
    logged=assert_private(caplog);assert len(logged)==1
    assert 'avatar_helper_called=True' in logged[0].getMessage()
    assert ('picture_claim_present='+str('picture' in claims)) in logged[0].getMessage()
@pytest.mark.parametrize('source,uploaded,saved_id',[('uploaded',PRIVATE,'PRIVATE_USER_ID'),('google',None,'PRIVATE_USER_ID'),('fallback',None,'other-user'),('fallback',None,None)])
def test_selection_no_identity_url_or_mutation(caplog,source,uploaded,saved_id,old_helper):
    caplog.set_level(logging.INFO);user=SimpleNamespace(id='PRIVATE_USER_ID',is_authenticated=True,profile_photo=uploaded)
    with website.app.test_request_context():
        if saved_id:session[avatar.SESSION_KEY]={'website_user':saved_id,'url':PRIVATE}
        before=dict(session);avatar.log_authenticated_avatar_state(user);assert dict(session)==before
        assert avatar.current_user_picture(user,lambda v:v)==old_helper['current_user_picture'](SimpleNamespace(**vars(user),get_id=lambda:user.id),lambda v:v)
    logged=assert_private(caplog);assert len(logged)==1 and 'navbar_source='+source in logged[0].getMessage()
def test_anonymous_not_logged(caplog):
    caplog.set_level(logging.INFO)
    with website.app.test_request_context():avatar.log_authenticated_avatar_state(SimpleNamespace(is_authenticated=False))
    assert not records(caplog)
@pytest.mark.parametrize('fallback',[False,True])
def test_only_existing_userinfo_fallback_and_next_request(setup,monkeypatch,caplog,fallback):
    caplog.set_level(logging.INFO);client,claims,uid=setup;calls=[];claims['picture']=PRIVATE
    if not fallback:claims.pop('picture')
    monkeypatch.setattr(website.google,'authorize_access_token',lambda:{'userinfo':None if fallback else claims,'id_token':'synthetic-id-only'})
    def userinfo(*args,**kwargs):calls.append(True);return SimpleNamespace(json=lambda:claims)
    monkeypatch.setattr(website.google,'get',userinfo)
    assert client.get('/google/callback').status_code==302 and len(calls)==int(fallback)
    assert client.get('/garage').status_code==200
    stages=[dict(part.split('=',1) for part in r.getMessage().split()[1:]) for r in assert_private(caplog)]
    assert [s['stage'] for s in stages]==['google_userinfo','google_callback','google_callback_exit','authenticated_request']
    assert stages[0]['google_userinfo_fallback_attempted']==str(fallback)
    assert stages[1]['avatar_stored']==str(fallback)
    assert stages[3]['navbar_source']==('google' if fallback else 'fallback')


def test_callback_failure_reports_helper_not_called(setup,monkeypatch,caplog):
    caplog.set_level(logging.INFO)
    client,claims,uid=setup
    def fail():
        raise RuntimeError('synthetic OAuth failure')
    monkeypatch.setattr(website.google,'authorize_access_token',fail)
    assert client.get('/google/callback').status_code==302
    logged=assert_private(caplog)
    assert len(logged)==1
    assert logged[0].getMessage()=='avatar_diagnostic stage=google_callback_exit avatar_helper_called=False'
