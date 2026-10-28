def test_legacy_support_deletion_intake_redirects_to_verified_flow():
 import app as website
 from models.models import db,HelpReport
 with website.app.app_context():
  db.create_all();before=HelpReport.query.count();client=website.app.test_client()
  page=client.get('/help');assert b'/account-deletion' in page.data
  response=client.post('/help',data={'email':'synthetic@example.invalid','category':'Account Deletion','message':'Request deletion'})
  assert response.status_code==303 and response.location.endswith('/account-deletion')
  assert HelpReport.query.count()==before
