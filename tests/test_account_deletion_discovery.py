"""Navigation and legacy Help redirect must not invoke deletion/report persistence."""
import uuid
import pytest
from html.parser import HTMLParser
import re

class Node:
    def __init__(self, tag='', attrs=None, parent=None):
        self.tag=tag;self.attrs=attrs or {};self.parent=parent;self.children=[]
    def __getitem__(self, key):return self.attrs[key]
    def get_text(self, separator='', strip=False):
        values=[]
        def read(node):
            for child in node.children:
                if isinstance(child,str):values.append(child.strip() if strip else child)
                else:read(child)
        read(self);return separator.join(x for x in values if x)

class Document(HTMLParser):
    def __init__(self, html):
        super().__init__();self.root=Node();self.stack=[self.root];self.nodes=[]
        self.feed(html.decode() if isinstance(html,bytes) else html)
    def handle_starttag(self, tag, attrs):
        node=Node(tag,dict(attrs),self.stack[-1]);self.stack[-1].children.append(node);self.nodes.append(node)
        if tag not in {'input','meta','link','img','br','hr','source','wbr'}:self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self, data):self.stack[-1].children.append(data)
    def select(self, selector):
        parts=re.findall(r'(?:[^\s\[]|\[[^\]]*\])+',selector)
        def matches(node, part):
            if part.startswith('#'):return node.attrs.get('id')==part[1:]
            if part.startswith('.'):return part[1:] in node.attrs.get('class','').split()
            match=re.fullmatch(r'([a-z]*)?(?:\[([^=]+)="([^"]*)"\])?',part)
            return bool(match) and (not match[1] or node.tag==match[1]) and (not match[2] or node.attrs.get(match[2])==match[3])
        found=[]
        for node in self.nodes:
            if not matches(node,parts[-1]):continue
            parent=node.parent;ok=True
            for part in reversed(parts[:-1]):
                while parent and not matches(parent,part):parent=parent.parent
                if not parent:ok=False;break
                parent=parent.parent
            if ok:found.append(node)
        return found
    def select_one(self, selector):
        values=self.select(selector);return values[0] if values else None


def links(html, selector):
    return Document(html).select(selector)


def test_logged_out_footer_on_home_and_help(monkeypatch):
    import app as website
    from models.models import db
    with website.app.app_context():
        db.create_all()
        client = website.app.test_client()
        for path in ['/', '/help', '/account-deletion']:
            response = client.get(path)
            assert response.status_code == 200
            found = links(response.data, 'footer a[href="/account-deletion"]')
            assert len(found) == 1 and found[0].get_text(' ', strip=True) == 'Account Deletion'
            assert not links(response.data, '#userMenu')


@pytest.mark.parametrize('role', ['user', 'mechanic'])
def test_logged_in_menu_and_profile_links_preserve_existing_access(role, monkeypatch):
    import app as website
    from models.models import User, db
    from flask import g
    import services.account_deletion_client as deletion
    def no_delete_call(*args, **kwargs):
        raise AssertionError('Navigation invoked deletion API')
    monkeypatch.setattr(deletion, 'public_call', no_delete_call)
    monkeypatch.setattr(deletion, 'admin_call', no_delete_call)
    with website.app.app_context():
        db.create_all()
        u = User(username='nav-'+uuid.uuid4().hex[:8], email=uuid.uuid4().hex+'@example.invalid', password='synthetic', role=role, is_banned=False)
        db.session.add(u); db.session.commit()
        c = website.app.test_client()
        with c.session_transaction() as saved:
            saved['_user_id'] = str(u.id); saved['_fresh'] = True
        g.pop('_login_user', None)
        response = c.get('/profile')
        assert response.status_code == 200
        soup = Document(response.data)
        assert soup.select_one('#userMenu a[href="/profile"]')
        assert soup.select_one('#userMenu a[href="/account-deletion"]').get_text(' ', strip=True) == 'Account Deletion'
        assert soup.select_one('.profile-actions a[href="/account-deletion"]').get_text(strip=True) == 'Account Deletion'
        button = soup.select_one('[aria-controls="userMenu"]')
        assert button['type'] == 'button' and button['aria-expanded'] == 'false' and button['aria-label'] == 'Account menu'
        target = c.get('/account-deletion')
        assert target.status_code == 200 and b'No automatic verification or completion email is sent' in target.data


def test_help_deletion_choice_is_native_get_link_not_generic_report_category():
    import app as website
    from models.models import db
    with website.app.app_context():
        db.create_all()
        c = website.app.test_client();page = c.get('/help')
        soup = Document(page.data)
        choice = soup.select_one('#account-deletion a[href="/account-deletion"]')
        assert choice.get_text(strip=True) == 'Delete AMPYAN account and associated data'
        assert not soup.select('select[name="category"] option[value="Account Deletion"]')
        assert soup.select_one('label[for="help-report-category"]')
        assert c.get(choice['href']).status_code == 200


@pytest.mark.parametrize('path,as_json', [('/help',False),('/api/help-report',True)])
def test_legacy_deletion_selection_redirects_before_any_report_or_deletion_work(path, as_json, monkeypatch):
    import app as website
    from models.models import db, HelpReport
    with website.app.app_context():
        db.create_all();before=HelpReport.query.count()
        def forbidden(*args, **kwargs):
            raise AssertionError('Legacy deletion navigation tried to persist a HelpReport')
        monkeypatch.setattr(website, 'HelpReport', forbidden)
        client=website.app.test_client()
        # Deliberately no message/email: deletion navigation must not require report fields.
        response=client.post(path,**({'json':{'category':'Account Deletion'}} if as_json else {'data':{'category':'Account Deletion'}}))
        assert response.status_code==303 and response.location.endswith('/account-deletion')
        assert HelpReport.query.count()==before
