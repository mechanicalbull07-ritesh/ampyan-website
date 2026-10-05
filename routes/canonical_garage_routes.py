"""Website presentation and validated inputs for the canonical Garage API.

The former local Garage implementation is retained, but is not registered.
"""
from datetime import datetime, timezone
from uuid import uuid4
from flask import Blueprint, render_template, request, redirect, session, jsonify, flash
from flask_login import login_required, current_user
from models.models import Car
from services.canonical_garage_client import call, connect, create_garage_account, GarageError
from services.garage_presentation import checklist_rows
from services.analytics_service import safe_track_event, action_event_id

garage_bp = Blueprint('garage', __name__)
TRANSMISSIONS = ('UNKNOWN','MANUAL','AMT','TORQUE_CONVERTER_AT','CVT','DCT','E_CVT','EV_SINGLE_SPEED','OTHER')
SYMPTOMS = {'brake_noise':'Brake noise', 'weak_battery_start':'Weak battery start', 'clutch_slipping':'Clutch slipping',
 'suspension_noise':'Suspension noise','ac_cooling_issue':'Poor air conditioning','tyre_uneven_wear':'Uneven tyre wear',
 'brake_failure':'Brake failure','engine_overheating':'Engine overheating','tyre_crack_bulge':'Tyre crack or bulge'}
SERVICE_TYPES = ('Periodic service','General service','Engine oil change','Brake work','Tyre work','Battery','AC service',
 'Suspension','Clutch','Engine','Transmission','Hybrid system','EV system','Other')

def path(car_id, suffix=''):
    return f'/api/garage/cars/{car_id}' + suffix

def screen(view, **kwargs):
    return render_template('canonical_garage.html', view=view, transmissions=TRANSMISSIONS,
        symptoms=SYMPTOMS, service_types=SERVICE_TYPES, form=request.form,
        operation_id=request.form.get('idempotency_key') or str(uuid4()),
        observed_at=request.form.get('observed_at') or datetime.now(timezone.utc).isoformat(), **kwargs)

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
    cars = call('/api/garage/cars').get('cars', [])
    legacy_count = Car.query.filter_by(owner_id=current_user.id).count()
    return screen('garage', cars=cars, legacy_count=legacy_count)

@garage_bp.route('/my-car-health')
@garage_bp.route('/garage-dashboard')
@login_required
def garage_dashboard():
    cars = call('/api/garage/cars').get('cars', [])
    if not cars:
        return screen('garage', cars=[], legacy_count=Car.query.filter_by(owner_id=current_user.id).count())
    selected = request.args.get('car_id', type=int) or session.get('garage_selected') or cars[0]['id']
    if selected not in [c['id'] for c in cars]:
        raise GarageError(404)
    data = call(path(selected, '/health?read_only=1'))
    mileage = call(path(selected, '/mileage'))
    health = data.get('health') or {}
    page = screen('health', cars=cars, car=data['car'], health=health, mileage=mileage.get('mileage') or {},
                  rows=checklist_rows(health.get('service_checklist') or {}), configuration=data.get('configuration') or {})
    safe_track_event('car_health_viewed', {'feature':'car_health'})
    return page

@garage_bp.route('/add-car', methods=['GET','POST'])
@login_required
def add_car():
    if request.method == 'POST':
        payload = {k:request.form[k] for k in ('brand','model','fuel_type','registration_year') if k in request.form}
        if not all(payload.get(k) for k in ('brand','model','fuel_type','registration_year')):
            raise GarageError(400)
        payload['transmission'] = request.form.get('transmission') or 'UNKNOWN'
        payload['current_odometer_km'] = integer('current_odometer_km')
        if payload['transmission'] not in TRANSMISSIONS:
            raise GarageError(400)
        call('/api/garage/cars','POST',payload)
        event = {'feature':'vehicle'}
        event_id = action_event_id(request.form.get('analytics_request_token'))
        if event_id:
            event['event_id'] = event_id
        safe_track_event('vehicle_added', event)
        return redirect('/garage')
    return screen('add')

@garage_bp.route('/set-default-car/<int:car_id>', methods=['POST'])
@login_required
def set_default_car(car_id):
    call(path(car_id))
    session['garage_selected'] = car_id
    return redirect('/garage-dashboard')

@garage_bp.route('/delete-car/<int:car_id>', methods=['POST'])
@login_required
def delete_car(car_id):
    call(path(car_id),'DELETE')
    if session.get('garage_selected') == car_id:
        session.pop('garage_selected',None)
    return redirect('/garage')

def integer(key):
    try:
        value = int(request.form[key])
        if value < 0:
            raise ValueError()
        return value
    except (KeyError,ValueError):
        raise GarageError(400) from None

@garage_bp.route('/edit-car/<int:car_id>', methods=['GET','POST'])
@login_required
def edit_car(car_id):
    car = call(path(car_id))['car']
    if request.method == 'POST':
        action = request.form.get('section')
        if action == 'configuration':
            return save_configuration(car_id, car)
        if action == 'odometer':
            payload = dict(actual_km=integer('actual_km'), user_confirmed=request.form.get('user_confirmed')=='yes',
                source='MANUAL', timezone='Asia/Kolkata', observed_at=request.form.get('observed_at'),
                idempotency_key=request.form.get('idempotency_key'), jump_acknowledged=request.form.get('jump_acknowledged')=='yes')
            if request.form.get('correction_of'):
                payload.update(correction_of=integer('correction_of'), correction_reason=request.form.get('correction_reason',''))
            call(path(car_id,'/mileage/confirmations'),'POST',payload)
        elif action == 'running':
            payload = dict(weekday_km=integer('weekday_km'), weekend_km=integer('weekend_km'),
                effective_date=request.form.get('effective_date'),timezone='Asia/Kolkata',provenance='USER_PROVIDED',
                idempotency_key=request.form.get('idempotency_key'))
            call(path(car_id,'/mileage/profiles'),'POST',payload)
        elif action == 'driving':
            known = request.form.get('driving_state') == 'KNOWN'
            city = integer('city_percent') if known else None
            highway = integer('highway_percent') if known else None
            if known and (city > 100 or highway > 100 or city + highway != 100):
                raise GarageError(400)
            value = dict(version=1,state='KNOWN' if known else 'LEARNING', source='USER_PROVIDED' if known else 'UNKNOWN',
                         city_percent=city,highway_percent=highway)
            if value != car.get('driving_input'):
                call(path(car_id),'PUT',{'driving_input':value})
        elif action == 'inputs':
            payload = {}
            if 'transmission' in request.form:
                transmission = request.form['transmission']
                if transmission not in TRANSMISSIONS:
                    raise GarageError(400)
                if transmission != car.get('transmission','UNKNOWN'):
                    payload['transmission'] = transmission
            for key in SYMPTOMS:
                if key in request.form:
                    raw = request.form[key]
                    if raw not in ('','true','false'):
                        raise GarageError(400)
                    value = None if raw == '' else raw == 'true'
                    if value != car.get(key):
                        payload[key] = value
            if 'usage_type' in request.form:
                value = request.form['usage_type'] or None
                if value not in (None,'normal','heavy load','taxi-commercial','mountain driving','towing'):
                    raise GarageError(400)
                if value != car.get('usage_type'):
                    payload['usage_type'] = value
            if payload:
                call(path(car_id),'PUT',payload)
        else:
            raise GarageError(400)
        flash('Saved. Car Health has been refreshed.')
        return redirect(f'/garage-dashboard?car_id={car_id}')
    mileage = call(path(car_id,'/mileage'))
    configuration = call(path(car_id, '/configuration'))['configuration']
    return screen('edit', car=car, mileage=mileage.get('mileage') or {}, history=mileage.get('history') or {}, configuration=configuration)

def save_configuration(car_id, car):
    configuration = call(path(car_id, '/configuration'))['configuration']
    error = None
    status = 400
    fields = {f['key']: f for f in configuration['fields']}
    try:
        revision = integer('setup_revision')
        if revision != configuration['revision']:
            raise GarageError(409)
        changes = {}
        for name, raw in request.form.items():
            if not name.startswith('setup.'):
                continue
            key = name[len('setup.'):]
            field = fields.get(key)
            if field is None or raw not in {o['value'] for o in field['options']}:
                raise GarageError(400)
            if raw != field['value']:
                value = {'unknown':None, 'true':True, 'false':False}.get(raw, raw)
                changes[key] = value
        if changes:
            call(path(car_id, '/configuration'), 'PATCH', {'revision':revision, 'changes':changes})
        return redirect('/garage-dashboard?car_id=' + str(car_id))
    except GarageError as exc:
        status = exc.status
        error = ('Vehicle setup changed. Your selections are retained; review the current details before retrying.'
                 if status == 409 else 'Setup was not saved. Check the selected details and any conflicting saved confirmations.'
                 if status == 400 else exc.message)
    mileage = call(path(car_id, '/mileage'))
    return screen('edit', car=car, configuration=configuration, setup_error=error,
        mileage=mileage.get('mileage') or {}, history=mileage.get('history') or {}), status


@garage_bp.route('/garage/cars/<int:car_id>/services', methods=['GET','POST'])
@login_required
def service_history(car_id):
    car = call(path(car_id))['car']
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        if service_type not in SERVICE_TYPES:
            raise GarageError(400)
        payload = dict(service_type=service_type,service_date=request.form.get('service_date'),
            odometer_km=integer('odometer_km'),qualifying_main_service=request.form.get('qualifying_main_service')=='yes',
            parts_replaced=[p.strip() for p in request.form.get('parts_replaced','').splitlines() if p.strip()],
            notes=request.form.get('notes',''))
        call(path(car_id,'/service-records'),'POST',payload)
        return redirect(f'/garage/cars/{car_id}/services')
    records = call(path(car_id,'/service-records')).get('service_records',[])
    return screen('services',car=car,records=records)

@garage_bp.app_template_filter('garage_km')
def garage_km(value):
    if isinstance(value, (int,float)):
        return f'{value:,.2f}'.rstrip('0').rstrip('.')
    return 'Unknown'
