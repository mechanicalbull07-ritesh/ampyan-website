"""Read-only Website presentation for the authoritative App Garage API."""
from flask import Blueprint, render_template, request, redirect, session, jsonify
from flask_login import login_required, current_user
from models.models import Car
from services.canonical_garage_client import call, connect, create_garage_account, GarageError
from services.garage_presentation import checklist_rows
from services.analytics_service import safe_track_event

garage_bp = Blueprint('garage', __name__)
def path(car_id, suffix=''):
    return f'/api/garage/cars/{car_id}' + suffix

def read_cars():
    cars = call('/api/garage/cars').get('cars')
    if not isinstance(cars, list) or any(not isinstance(car, dict) or type(car.get('id')) is not int for car in cars):
        raise GarageError(503)
    return cars

def screen(view, **kwargs):
    return render_template('canonical_garage.html', view=view, **kwargs)

@garage_bp.app_errorhandler(GarageError)
def garage_error(exc):
    if request.path.startswith('/api/'):
        return jsonify(success=False, message=exc.message), exc.status
    return screen('error', error=exc.message), exc.status

@garage_bp.route('/garage/connect', methods=['GET','POST'])
@login_required
def connect_garage():
    if request.method == 'POST':
        if request.form.get('create_account') == 'yes':
            create_garage_account(request.form.get('password',''))
        else:
            connect(password=request.form.get('password',''))
        return redirect('/garage')
    return screen('connect')

@garage_bp.route('/garage')
@login_required
def garage():
    saved = session.get('garage_credentials') or {}
    if not saved.get('token') or saved.get('website_user') != str(current_user.get_id()):
        return screen('onboarding')
    cars = read_cars()
    legacy_count = Car.query.filter_by(owner_id=current_user.id).count()
    return screen('garage', cars=cars, legacy_count=legacy_count) if cars else screen('onboarding')

@garage_bp.route('/my-car-health')
@garage_bp.route('/garage-dashboard')
@login_required
def garage_dashboard():
    saved = session.get('garage_credentials') or {}
    if not saved.get('token') or saved.get('website_user') != str(current_user.get_id()):
        return screen('onboarding')
    cars = read_cars()
    if not cars:
        return screen('onboarding')
    selected = request.args.get('car_id', type=int) or session.get('garage_selected') or cars[0]['id']
    if selected not in [c['id'] for c in cars]:
        raise GarageError(404)
    data = call(path(selected, '/health?read_only=1'))
    if not isinstance(data.get('car'), dict) or data['car'].get('id') != selected or not isinstance(data.get('health'), dict):
        raise GarageError(503)
    health = data['health']
    mileage_error = None
    try:
        mileage = call(path(selected, '/mileage'))
        if not isinstance(mileage.get('mileage'), dict):
            raise GarageError(503)
    except GarageError as exc:
        if exc.status not in (503, 429):
            raise
        mileage = {'mileage': {}}
        mileage_error = exc.message
    page = screen('health', cars=cars, car=data['car'], health=health, mileage=mileage.get('mileage') or {},
                  rows=checklist_rows(health.get('service_checklist') or {}), configuration=data.get('configuration') or {},
                  mileage_error=mileage_error)
    safe_track_event('car_health_viewed', {'feature':'car_health'})
    return page

@garage_bp.route('/add-car')
@login_required
def add_car():
    return screen('onboarding')

@garage_bp.route('/set-default-car/<int:car_id>', methods=['POST'])
@login_required
def set_default_car(car_id):
    # Selection belongs to the Website session, never to vehicle data.
    call(path(car_id))
    session['garage_selected'] = car_id
    return redirect('/garage-dashboard')

@garage_bp.route('/edit-car/<int:car_id>')
@login_required
def edit_car(car_id):
    call(path(car_id))  # Preserve ownership checks on bookmarked links.
    return redirect(f'/my-car-health?car_id={car_id}')

@garage_bp.route('/garage/cars/<int:car_id>/services')
@login_required
def service_history(car_id):
    car = call(path(car_id))['car']
    records = call(path(car_id, '/service-records')).get('service_records', [])
    return screen('services', car=car, records=records)

@garage_bp.app_context_processor
def app_acquisition():
    # Existing official destination, also used by the homepage.
    return {'ampyan_app_url': 'https://play.google.com/store/apps/details?id=com.ampyan.app'}

@garage_bp.app_template_filter('garage_km')
def garage_km(value):
    if isinstance(value, (int,float)):
        return f'{value:,.2f}'.rstrip('0').rstrip('.')
    return 'Not yet available'
