"""Temporary Website Community read-only containment. No schema, queue or replay state.
The early guard must be registered before every other application request callback.
"""
import os
import re
from flask import g,request,jsonify,make_response

NOTICE='Website Community is temporarily read-only. You can browse existing discussions; posting, replies, edits, deletion and voting are unavailable.'
MUTATION_ENDPOINTS={
 'community.create_post','community.create_car_community','community.edit_post',
 'community.delete_post','community.add_comment','community.remote_add_comment',
 'community.upvote','community.edit_comment','community.delete_comment',
 'community.api_create_community_post','community.api_update_community_post',
 'community.api_delete_community_post','community.api_create_community_reply',
 'admin.create_managed_persona','admin.admin_create_post_as_persona',
 'admin.admin_reply_as_persona','admin.delete_user'}
MUTATION_PAGES=re.compile(r'^/(?:create-post|(?:post|comment)/[0-9]+/(?:edit|delete)|add_comment/[0-9]+|upvote/[0-9]+|admin/delete-user/[0-9]+)$')

def public_name(value):
    name=str(value or '').strip()
    if not name or '@' in name or re.search(r'\d[\d\s()+.\-]{5,}\d',name):return 'Community Member'
    return name[:100]

def guarded():
    path=request.path.rstrip('/') or '/'
    if request.endpoint in MUTATION_ENDPOINTS or MUTATION_PAGES.fullmatch(path):return True
    if path=='/admin/community' or path.startswith('/admin/community/'):return True
    if request.method not in ('GET','HEAD','OPTIONS'):
        return path in ('/community','/api/community') or path.startswith(('/community/','/api/community/'))
    return False

def reject():
    path = request.path.rstrip('/') or '/'
    hold = os.environ.get('COMMUNITY_PUBLIC_READ_HOLD', 'false').lower() == 'true'
    community_read = (request.blueprint == 'community' or path in ('/community', '/api/community')
                      or path.startswith(('/community/', '/api/community/'))
                      or re.fullmatch(r'/post/[0-9]+(?:/.*)?', path))
    if hold and request.method in ('GET', 'HEAD') and community_read:
        # First request callback; never consult cache, identity, ORM or transport.
        g.community_read_only_rejected = True
        message = 'Community is temporarily unavailable during maintenance. Other website features remain available.'
        if request.path.startswith('/api/') or request.accept_mimetypes.best == 'application/json':
            response = jsonify(status='error', code='COMMUNITY_MAINTENANCE', message=message)
            response.status_code = 503
        else:
            response = make_response('<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1">'
                                     '<title>Community maintenance</title><main><h1>Community is temporarily unavailable</h1>'
                                     '<p>' + message + '</p><a href="/">AMPYAN home</a></main></html>', 503)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Community-Mode'] = 'maintenance-hold'
        return response
    if not guarded():return None
    # No current_user, form/files, session, models, uploads or HTTP access here.
    g.community_read_only_rejected=True
    if request.path.startswith('/api/') or request.accept_mimetypes.best=='application/json':
        response=jsonify(status='error',code='COMMUNITY_READ_ONLY',message=NOTICE)
        response.status_code=503
    else:
        response=make_response('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>AMPYAN Community — read-only</title><main><h1>Community is read-only</h1>'
            '<p>'+NOTICE+'</p><a href="/community">Browse Community</a></main></html>',503)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Community-Mode']='read-only'
    return response

def install(app):
    if app.before_request_funcs.get(None):
        raise RuntimeError('Community read-only guard must be installed first')
    app.before_request(reject)
    app.after_request(response_policy)
    app.context_processor(lambda:{'community_read_only':True,'community_read_only_notice':NOTICE})
    app.add_template_filter(public_name,'community_public_name')


def response_policy(response):
    path = request.path.rstrip('/') or '/'
    if (request.blueprint == 'community' or path in ('/community', '/api/community')
            or path.startswith(('/community/', '/api/community/'))
            or re.fullmatch(r'/post/[0-9]+(?:/.*)?', path)):
        response.headers['Cache-Control'] = 'private, no-store, max-age=0'
        response.vary.add('Authorization')
    return response
