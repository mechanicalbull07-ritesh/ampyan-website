import pytest
from tests.csrf_source_checker import unprotected_forms

FIELD='<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
MACRO='{% macro token() %}'+FIELD+'{% endmacro %}'

@pytest.mark.parametrize('source',[
 '<form method="POST">'+FIELD+'</form>',
 "<form method='post'><input type='hidden' name='csrf_token' value='{{ csrf_token() }}'></form>",
 MACRO+'<form method="post">{{ token() }}</form>',
])
def test_secure_forms_recognized(source):
    assert unprotected_forms(source)==[]

@pytest.mark.parametrize('source',[
 '<form method="post"></form>',
 '<form method="post">{{ token() }}</form>',
 '{% macro token() %}nothing{% endmacro %}<form method="post">{{ token() }}</form>',
 MACRO+'<form method="post"></form>',
 '<form method="post"><!--'+FIELD+'--></form>',
 '<form method="post">{#'+FIELD+'#}</form>',
 '<form method="post">'+FIELD.replace('csrf_token()','fake_token()')+'</form>',
 '<form method="post">'+FIELD.replace('{{ csrf_token() }}','hardcoded')+'</form>',
 '<form method="post">'+FIELD.replace('type="hidden"','type="hidden" disabled')+'</form>',
 '<form method="post">'+FIELD.replace('name="csrf_token"','name="other"')+'</form>',
 '<form method="post">{% if false %}'+FIELD+'{% endif %}</form>',
 '{% macro token() %}{% if false %}'+FIELD+'{% endif %}{% endmacro %}<form method="post">{{ token() }}</form>',
 '<form method="post">'+FIELD,
])
def test_unprotected_forms_rejected(source):
    assert unprotected_forms(source)


def test_reviewed_dynamic_reply_token_pattern():
    from tests.csrf_source_checker import DYNAMIC_FIELD
    form='<form method="POST">'+DYNAMIC_FIELD+'</form>'
    assert unprotected_forms(form)==[]
    assert unprotected_forms(form.replace("escapeHtml", "untrustedValue"))
    assert unprotected_forms(form.replace("csrf-token", "other-meta"))
