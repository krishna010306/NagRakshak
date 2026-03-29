import math
import json
from datetime import timedelta
from math import radians, sin, cos, sqrt, atan2

from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError

from .models import AmbulanceDriver, EmergencyAlert, Hospital, User, Volunteer
from .models import ambulance, hospital, volunteer


FIRST_AID_STEPS = [
    "Keep the patient calm and still.",
    "Remove rings, bangles, and tight clothing near bite area.",
    "Do not cut, suck, or apply ice on the bite.",
    "Keep bitten limb below heart level and avoid walking.",
    "Reach anti-venom capable hospital immediately.",
]

DRIVER_ACCEPT_TIMEOUT_MINUTES = 5
MAX_DRIVER_ATTEMPTS = 3


def _serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.contact,
        "contact": user.contact,
        "email": user.email,
        "role": user.role,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "eme_contact": user.eme_contact,
    }


def _serialize_ambulance(driver):
    return {
        "id": driver.id,
        "name": driver.name,
        "phone": driver.contact,
        "contact": driver.contact,
        "email": driver.email,
        "latitude": driver.latitude,
        "longitude": driver.longitude,
    }


def _serialize_volunteer(vol):
    return {
        "id": vol.id,
        "name": vol.name,
        "phone": vol.contact,
        "contact": vol.contact,
        "email": vol.email,
        "ngo_name": vol.ngo_name,
        "latitude": vol.latitude,
        "longitude": vol.longitude,
    }


def _resolve_user(payload):
    user_id = payload.get("user_id")
    email = str(payload.get("email") or "").strip().lower()
    phone = str(payload.get("phone") or payload.get("contact") or "").strip()

    if user_id not in (None, ""):
        try:
            return User.objects.filter(id=int(user_id)).first()
        except (TypeError, ValueError):
            return None

    if email:
        user = User.objects.filter(email__iexact=email).first()
        if user:
            return user

    if phone:
        user = User.objects.filter(contact=phone).first()
        if user:
            return user
        return None

    return None


def _resolve_user_location(payload, user):
    lat = payload.get("lat")
    lng = payload.get("lng")

    if lat not in (None, "") and lng not in (None, ""):
        return _to_float(lat, "lat"), _to_float(lng, "lng")

    if user and user.latitude is not None and user.longitude is not None:
        return float(user.latitude), float(user.longitude)

    raise ValueError("lat/lng is required or user profile location must be set")


@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    data     = json.loads(request.body)
    email    = data.get('email', '')
    password = data.get('password', '')

    # Check users table first
    try:
        u = users.objects.get(email=email, password=password)
        return JsonResponse({
            'status': 'success',
            'role':   u.role,
            'user':   {'id': u.id, 'name': u.name, 'email': u.email}
        })
    except users.DoesNotExist:
        pass

    # Check ambulance table
    try:
        a = ambulance.objects.get(email=email, password=password)
        return JsonResponse({
            'status': 'success',
            'role':   'driver',
            'user':   {'id': a.id, 'name': a.name, 'email': a.email}
        })
    except ambulance.DoesNotExist:
        pass

    # Check volunteer table
    try:
        v = volunteer.objects.get(email=email, password=password)
        return JsonResponse({
            'status': 'success',
            'role':   'volunteer',
            'user':   {'id': v.id, 'name': v.name, 'email': v.email}
        })
    except volunteer.DoesNotExist:
        pass

    return JsonResponse({'status': 'error', 'message': 'Invalid email or password'})
    """Login with email + password."""
    email = str(request.data.get("email") or request.data.get("username") or "").strip().lower()
    password = str(request.data.get("password") or "").strip()

    if not email or not password:
        return Response(
            {
                "status": "error",
                "message": "email and password are required",
                "next_screen": "login",
                "user": None,
            },
            status=400,
        )

    user = User.objects.filter(email__iexact=email).first()
    if not user or not check_password(password, user.password):
        return Response(
            {
                "status": "error",
                "message": "Invalid email or password",
                "next_screen": "login",
                "user": None,
            },
            status=401,
        )

    return Response(
        {
            "status": "success",
            "message": "Login successful",
            "next_screen": "sos",
            "role": user.role,
            "user": _serialize_user(user),
        }
    )


@api_view(["POST"])
def register_user(request):
    """Create or update user profile from signup using email/password."""
    email = str(request.data.get("email") or "").strip().lower()
    password = str(request.data.get("password") or "").strip()
    contact = str(request.data.get("contact") or request.data.get("phone") or "").strip()
    name = str(request.data.get("name") or "User").strip() or "User"
    role = str(request.data.get("role") or "victim").strip().lower()
    eme_contact = str(request.data.get("eme_contact") or "").strip()

    latitude = request.data.get("latitude", request.data.get("lat"))
    longitude = request.data.get("longitude", request.data.get("lng"))

    if not email or not password:
        return Response({"status": "error", "message": "email and password are required"}, status=400)

    if latitude in (None, "") or longitude in (None, ""):
        return Response({"status": "error", "message": "latitude and longitude are required"}, status=400)

    # Validate coordinates
    parsed_latitude = _to_float(latitude, "latitude")
    parsed_longitude = _to_float(longitude, "longitude")
    
    if not (-90 <= parsed_latitude <= 90 and -180 <= parsed_longitude <= 180):
        return Response({"status": "error", "message": "Invalid coordinates"}, status=400)

    # Validate phone format (basic check)
    if contact and len(contact) < 10:
        return Response({"status": "error", "message": "Phone number must be at least 10 digits"}, status=400)

    valid_roles = {choice[0] for choice in User.ROLE_CHOICES}
    if role not in valid_roles:
        role = "victim"

    user = User.objects.filter(email__iexact=email).first()
    if not user and contact:
        user = User.objects.filter(contact=contact).first()

    created = False
    try:
        if not user:
            user = User.objects.create(
                name=name,
                contact=contact,
                email=email,
                password=make_password(password),
                role=role,
                latitude=parsed_latitude,
                longitude=parsed_longitude,
                eme_contact=eme_contact,
            )
            created = True
        else:
            user.name = name
            user.contact = contact or user.contact
            user.email = email
            user.password = make_password(password)
            user.role = role
            user.eme_contact = eme_contact
            user.latitude = parsed_latitude
            user.longitude = parsed_longitude
            user.save()
    except IntegrityError:
        return Response({"status": "error", "message": "Email already exists"}, status=400)

    return Response(
        {
            "status": "success",
            "created": created,
            "role": user.role,
            "user": _serialize_user(user),
        },
        status=201 if created else 200,
    )


@api_view(["POST"])
def role_lookup(request):
    """Compatibility endpoint for app login-role/user-role/role routes."""
    user = _resolve_user(request.data)
    if not user:
        return Response({"message": "User not found. Provide user_id/email/phone/contact"}, status=404)

    return Response({"status": "success", "role": user.role, "user": _serialize_user(user)})


@api_view(["GET", "POST"])
def users_endpoint(request):
    """Compatibility endpoint for /api/users/ and /api/user/by-phone/."""
    if request.method == "POST":
        return register_user(request)

    phone = str(request.query_params.get("phone") or "").strip()
    email = str(request.query_params.get("email") or "").strip().lower()
    contact = str(request.query_params.get("contact") or "").strip()
    queryset = User.objects.all()
    if phone:
        queryset = queryset.filter(contact=phone)
    if email:
        queryset = queryset.filter(email__iexact=email)
    if contact:
        queryset = queryset.filter(contact=contact)

    data = [_serialize_user(user) for user in queryset.order_by("-id")[:50]]
    return Response(data)


@csrf_exempt
def register_ambulance(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    name = data.get('name', '')
    email = str(data.get('email', '')).strip().lower()
    password = data.get('password', '')
    contact = data.get('contact', '')
    lat = data.get('latitude', 0)
    lng = data.get('longitude', 0)

    if not email or not password:
        return JsonResponse({'status': 'error', 'message': 'Email and password required'}, status=400)

    if ambulance.objects.filter(email=email).exists():
        return JsonResponse({'status': 'error', 'message': 'Email already registered'}, status=400)

    ambulance.objects.create(
        name=name,
        email=email,
        password=password,
        contact=contact,
        latitude=lat,
        longitude=lng,
    )

    return JsonResponse({'status': 'success', 'message': 'Ambulance registered'})


@api_view(["POST"])
def register_volunteer(request):
    email = str(request.data.get("email") or "").strip().lower()
    password = str(request.data.get("password") or "").strip()
    contact = str(request.data.get("contact") or request.data.get("phone") or "").strip()
    name = str(request.data.get("name") or "Volunteer").strip() or "Volunteer"
    ngo_name = str(request.data.get("ngo_name") or "").strip()
    latitude = request.data.get("latitude", request.data.get("lat"))
    longitude = request.data.get("longitude", request.data.get("lng"))

    if not email or not password:
        return Response({"status": "error", "message": "email and password are required"}, status=400)

    if latitude in (None, "") or longitude in (None, ""):
        return Response({"status": "error", "message": "latitude and longitude are required"}, status=400)

    parsed_latitude = _to_float(latitude, "latitude")
    parsed_longitude = _to_float(longitude, "longitude")
    if not (-90 <= parsed_latitude <= 90 and -180 <= parsed_longitude <= 180):
        return Response({"status": "error", "message": "Invalid coordinates"}, status=400)

    if contact and len(contact) < 10:
        return Response({"status": "error", "message": "Phone number must be at least 10 digits"}, status=400)

    volunteer = Volunteer.objects.filter(email__iexact=email).first()
    if not volunteer and contact:
        volunteer = Volunteer.objects.filter(contact=contact).first()

    created = False
    try:
        if not volunteer:
            volunteer = Volunteer.objects.create(
                name=name,
                email=email,
                password=make_password(password),
                ngo_name=ngo_name,
                contact=contact,
                latitude=parsed_latitude,
                longitude=parsed_longitude,
            )
            created = True
        else:
            volunteer.name = name
            volunteer.email = email
            volunteer.password = make_password(password)
            volunteer.ngo_name = ngo_name
            volunteer.contact = contact or volunteer.contact
            volunteer.latitude = parsed_latitude
            volunteer.longitude = parsed_longitude
            volunteer.save()
    except IntegrityError:
        return Response({"status": "error", "message": "Email already exists"}, status=400)

    return Response(
        {
            "status": "success",
            "message": "Volunteer registered",
            "created": created,
            "volunteer": _serialize_volunteer(volunteer),
        },
        status=201 if created else 200,
    )


def _to_float(value, name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {name}")


def _parse_vehicle(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"yes", "y", "true", "1"}:
        return True
    if normalized in {"no", "n", "false", "0"}:
        return False
    return None


def _distance_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def _nearest_hospital(user_lat, user_lng, antivenom_only=True):
    if not (-90 <= user_lat <= 90 and -180 <= user_lng <= 180):
        raise ValueError("Invalid coordinates")
    
    hospitals = Hospital.objects.filter(antivenom=True) if antivenom_only else Hospital.objects.all()
    nearest = None
    min_distance = float("inf")

    for hospital in hospitals:
        if not (-90 <= hospital.latitude <= 90 and -180 <= hospital.longitude <= 180):
            continue
        distance = _distance_km(user_lat, user_lng, hospital.latitude, hospital.longitude)
        if distance < min_distance:
            min_distance = distance
            nearest = hospital

    if nearest:
        return nearest, round(min_distance, 2)
    return None, None


def nearest_driver(user_lat, user_lng):
    if not (-90 <= user_lat <= 90 and -180 <= user_lng <= 180):
        raise ValueError("Invalid coordinates")
    
    nearest = None
    min_distance = float("inf")

    for driver in AmbulanceDriver.objects.all():
        if not (-90 <= driver.latitude <= 90 and -180 <= driver.longitude <= 180):
            continue
        distance = _distance_km(user_lat, user_lng, driver.latitude, driver.longitude)
        if distance < min_distance:
            min_distance = distance
            nearest = driver

    if nearest:
        return nearest, round(min_distance, 2)
    return None, None


def _nearest_volunteer(user_lat, user_lng):
    if not (-90 <= user_lat <= 90 and -180 <= user_lng <= 180):
        raise ValueError("Invalid coordinates")
    
    nearest = None
    min_distance = float("inf")

    for volunteer in Volunteer.objects.all():
        if not (-90 <= volunteer.latitude <= 90 and -180 <= volunteer.longitude <= 180):
            continue
        distance = _distance_km(user_lat, user_lng, volunteer.latitude, volunteer.longitude)
        if distance < min_distance:
            min_distance = distance
            nearest = volunteer

    if nearest:
        return nearest, round(min_distance, 2)
    return None, None


def _rank_drivers_by_distance(user_lat, user_lng, excluded_driver_ids=None):
    excluded_driver_ids = set(excluded_driver_ids or [])
    ranked = []
    for driver in AmbulanceDriver.objects.all():
        if driver.id in excluded_driver_ids:
            continue
        distance = _distance_km(user_lat, user_lng, driver.latitude, driver.longitude)
        ranked.append((driver, round(distance, 2)))
    ranked.sort(key=lambda item: item[1])
    return ranked


def _notify_next_driver(alert):
    if alert.driver_attempt_count >= MAX_DRIVER_ATTEMPTS:
        return None, None

    attempted_ids = list(alert.attempted_driver_ids or [])
    ranked = _rank_drivers_by_distance(alert.latitude, alert.longitude, attempted_ids)
    if not ranked:
        return None, None

    driver, distance = ranked[0]
    attempted_ids.append(driver.id)

    alert.assigned_driver = driver
    alert.status = "ambulance_notified"
    alert.driver_notified_at = timezone.now()
    alert.driver_attempt_count = len(attempted_ids)
    alert.attempted_driver_ids = attempted_ids
    alert.save(
        update_fields=[
            "assigned_driver",
            "status",
            "driver_notified_at",
            "driver_attempt_count",
            "attempted_driver_ids",
        ]
    )
    return driver, distance


def _notify_volunteer(alert):
    nearest_volunteer, volunteer_distance = _nearest_volunteer(alert.latitude, alert.longitude)
    if not nearest_volunteer:
        alert.status = "pending"
        alert.save(update_fields=["status"])
        return None, None

    alert.assigned_volunteer = nearest_volunteer
    alert.status = "volunteer_notified"
    alert.save(update_fields=["assigned_volunteer", "status"])
    return nearest_volunteer, volunteer_distance


def _refresh_expired_driver_alerts():
    now = timezone.now()
    timeout_delta = timedelta(minutes=DRIVER_ACCEPT_TIMEOUT_MINUTES)

    for alert in EmergencyAlert.objects.filter(status="ambulance_notified"):
        notified_at = alert.driver_notified_at
        if notified_at and (now - notified_at) < timeout_delta:
            continue

        if alert.driver_attempt_count < MAX_DRIVER_ATTEMPTS:
            driver, _ = _notify_next_driver(alert)
            if driver:
                continue

        _notify_volunteer(alert)


def _sos_decision(payload):
    user = _resolve_user(payload)
    user_lat, user_lng = _resolve_user_location(payload, user)
    has_vehicle = _parse_vehicle(payload.get("vehicle"))

    if has_vehicle is None:
        raise ValueError("vehicle must be yes/no or true/false")

    patient_name = str(payload.get("name") or (user.name if user else "") or "User").strip()
    patient_phone = str(
        payload.get("phone")
        or payload.get("contact")
        or (user.contact if user and user.contact else "")
    ).strip()

    if user and (payload.get("lat") not in (None, "") and payload.get("lng") not in (None, "")):
        user.latitude = user_lat
        user.longitude = user_lng
        user.save(update_fields=["latitude", "longitude"])

    nearest_hospital, hospital_distance = _nearest_hospital(user_lat, user_lng, antivenom_only=True)
    if not nearest_hospital:
        nearest_hospital, hospital_distance = _nearest_hospital(user_lat, user_lng, antivenom_only=False)

    alert = EmergencyAlert.objects.create(
        patient_name=patient_name,
        patient_phone=patient_phone,
        latitude=user_lat,
        longitude=user_lng,
        snake_type=payload.get("snake_type", ""),
        has_vehicle=has_vehicle,
        assigned_hospital=nearest_hospital,
    )

    if has_vehicle:
        alert.status = "hospital_routed"
        alert.save(update_fields=["status"])
        hospital_data = None
        if nearest_hospital:
            hospital_data = {
                "id": nearest_hospital.id,
                "name": nearest_hospital.name,
                "lat": nearest_hospital.latitude,
                "lng": nearest_hospital.longitude,
                "phone": nearest_hospital.contact,
                "distance_km": hospital_distance,
                "has_antivenom": nearest_hospital.antivenom,
            }

        return {
            "alert_id": alert.id,
            "route": "self_transport",
            "first_aid": FIRST_AID_STEPS,
            "hospital_alerted": bool(nearest_hospital),
            "hospital": hospital_data,
            "using_saved_location": payload.get("lat") in (None, "") or payload.get("lng") in (None, ""),
            "message": "Proceed to nearest anti-venom hospital using navigation.",
        }

    nearest_driver, driver_distance = _notify_next_driver(alert)
    if nearest_driver:
        return {
            "alert_id": alert.id,
            "route": "ambulance",
            "first_aid": FIRST_AID_STEPS,
            "hospital_alerted": bool(nearest_hospital),
            "hospital": {
                "id": nearest_hospital.id,
                "name": nearest_hospital.name,
                "phone": nearest_hospital.contact,
            }
            if nearest_hospital
            else None,
            "ambulance_driver": {
                "id": nearest_driver.id,
                "name": nearest_driver.name,
                "phone": nearest_driver.contact,
                "distance_km": driver_distance,
            },
            "attempt": alert.driver_attempt_count,
            "wait_time_minutes": DRIVER_ACCEPT_TIMEOUT_MINUTES,
            "message": "Ambulance alerted. If not accepted in 5 minutes, system tries next driver (max 3), then volunteer.",
        }

    nearest_volunteer, volunteer_distance = _notify_volunteer(alert)
    if nearest_volunteer:
        return {
            "alert_id": alert.id,
            "route": "volunteer",
            "first_aid": FIRST_AID_STEPS,
            "hospital_alerted": bool(nearest_hospital),
            "hospital": {
                "id": nearest_hospital.id,
                "name": nearest_hospital.name,
                "phone": nearest_hospital.contact,
            }
            if nearest_hospital
            else None,
            "volunteer": {
                "id": nearest_volunteer.id,
                "name": nearest_volunteer.name,
                "phone": nearest_volunteer.contact,
                "distance_km": volunteer_distance,
            },
            "message": "Volunteer backup alerted due to ambulance unavailability.",
        }

    return {
        "alert_id": alert.id,
        "route": "hospital_only",
        "first_aid": FIRST_AID_STEPS,
        "hospital_alerted": bool(nearest_hospital),
        "hospital": {
            "id": nearest_hospital.id,
            "name": nearest_hospital.name,
            "phone": nearest_hospital.contact,
            "distance_km": hospital_distance,
        }
        if nearest_hospital
        else None,
        "message": "No ambulance/volunteer available right now. Move toward nearest hospital.",
    }


@api_view(["POST"])
def sos(request):
    try:
        return Response(_sos_decision(request.data))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception as exc:
        return Response({"error": f"Unexpected error: {exc}"}, status=500)


@api_view(["GET"])
def get_hospitals(request):
    hospitals = Hospital.objects.all()
    return Response(
        [
            {
                "id": h.id,
                "name": h.name,
                "lat": h.latitude,
                "lng": h.longitude,
                "phone": h.contact,
                "has_antivenom": h.antivenom,
            }
            for h in hospitals
        ]
    )


@api_view(["POST"])
def send_alert(request):
    try:
        payload = {
            "name": request.data.get("name", ""),
            "phone": request.data.get("phone", ""),
            "contact": request.data.get("contact", ""),
            "email": request.data.get("email", ""),
            "lat": request.data.get("lat"),
            "lng": request.data.get("lng"),
            "snake_type": request.data.get("snake_type", ""),
            "vehicle": request.data.get("vehicle", "no"),
        }
        result = _sos_decision(payload)
        return Response({"status": "success", **result})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception as exc:
        return Response({"error": str(exc)}, status=500)


@api_view(["POST"])
def nearest_hospital(request):
    try:
        user = _resolve_user(request.data)
        user_lat, user_lng = _resolve_user_location(request.data, user)
        nearest, distance = _nearest_hospital(user_lat, user_lng, antivenom_only=True)
        if not nearest:
            nearest, distance = _nearest_hospital(user_lat, user_lng, antivenom_only=False)

        if not nearest:
            return Response({"error": "No hospital found"}, status=404)

        return Response(
            {
                "id": nearest.id,
                "name": nearest.name,
                "lat": nearest.latitude,
                "lng": nearest.longitude,
                "phone": nearest.contact,
                "distance_km": distance,
                "has_antivenom": nearest.antivenom,
            }
        )
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)


@api_view(["POST"])
def smart_emergency(request):
    data = request.data.copy()
    _refresh_expired_driver_alerts()

    # App may send need_ambulance without explicit vehicle flag.
    if data.get("vehicle") in (None, "") and data.get("need_ambulance"):
        data["vehicle"] = "no"

    # If volunteer escalation is requested for an existing alert, handle directly.
    if data.get("need_volunteer"):
        alert_id = data.get("id")
        try:
            alert = EmergencyAlert.objects.get(id=alert_id)
        except EmergencyAlert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=404)

        nearest_volunteer, distance = _notify_volunteer(alert)
        if not nearest_volunteer:
            return Response({"message": "No volunteer available"}, status=404)
        return Response(
            {
                "status": "success",
                "type": "volunteer",
                "alert_id": alert.id,
                "volunteer": {
                    "id": nearest_volunteer.id,
                    "name": nearest_volunteer.name,
                    "phone": nearest_volunteer.contact,
                    "distance_km": distance,
                },
            }
        )

    try:
        return Response(_sos_decision(data))
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    except Exception as exc:
        return Response({"error": f"Unexpected error: {exc}"}, status=500)


def get_driver_requests(request):
    amb_id = request.GET.get('driver_id')
    try:
        amb = ambulance.objects.get(id=amb_id)
        alert = EmergencyAlert.objects.filter(
            assigned_driver=amb,
            status='ambulance_notified'
        ).order_by('-timestamp').first()
        if alert:
            return JsonResponse({
                'status':      'ambulance_notified',
                'alert_id':    alert.id,
                'victim_lat':  alert.latitude,
                'victim_lng':  alert.longitude,
                'victim_name': alert.patient_name,
                'victim_phone':alert.patient_phone,
            })
        return JsonResponse({'status': 'no_alert'})
    except ambulance.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


@api_view(["GET", "POST"])
def ambulance_requests(request):
    """Compatibility endpoint for app ambulance dispatch + polling."""
    if request.method == "POST":
        _refresh_expired_driver_alerts()
        data = request.data.copy()
        if data.get("vehicle") in (None, ""):
            data["vehicle"] = "no"
        data.setdefault("phone", data.get("victim_phone", ""))
        data.setdefault("name", data.get("victim_name", "User"))
        data.setdefault("snake_type", data.get("request_type", "unknown"))

        try:
            result = _sos_decision(data)
            return Response({"status": "success", **result})
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        except Exception as exc:
            return Response({"error": str(exc)}, status=500)

    return get_driver_requests(request)


@api_view(["POST"])
def accept_request(request):
    alert_id = request.data.get("id")
    accepted = request.data.get("accepted", True)

    if isinstance(accepted, str):
        accepted = accepted.strip().lower() in {"yes", "true", "1"}

    if not alert_id:
        return Response({"status": "error", "message": "Alert ID is required"}, status=400)

    try:
        alert = EmergencyAlert.objects.select_related("assigned_hospital", "assigned_driver").get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return Response({"status": "error", "message": "Alert not found"}, status=404)
    except (ValueError, TypeError):
        return Response({"status": "error", "message": "Invalid alert ID"}, status=400)

    if accepted:
        alert.status = "ambulance_accepted"
        alert.save(update_fields=["status"])
        
        hospital_data = None
        if alert.assigned_hospital:
            hospital_data = {
                "id": alert.assigned_hospital.id,
                "name": alert.assigned_hospital.name,
                "phone": alert.assigned_hospital.contact,
            }
        
        return Response(
            {
                "status": "success",
                "message": "Accepted. Hospital has been notified that victim is coming.",
                "alert_id": alert.id,
                "patient": {
                    "name": alert.patient_name,
                    "phone": alert.patient_phone,
                    "lat": alert.latitude,
                    "lng": alert.longitude,
                },
                "hospital": hospital_data,
                "next_screen": "victim_location_and_navigation",
            }
        )

    next_driver, next_driver_distance = _notify_next_driver(alert)
    if next_driver:
        return Response(
            {
                "status": "success",
                "message": "Driver declined. Request moved to next nearest ambulance driver.",
                "route": "ambulance",
                "attempt": alert.driver_attempt_count,
                "ambulance_driver": {
                    "id": next_driver.id,
                    "name": next_driver.name,
                    "phone": next_driver.contact,
                    "distance_km": next_driver_distance,
                },
            }
        )

    nearest_volunteer, volunteer_distance = _notify_volunteer(alert)
    if nearest_volunteer:
        return Response(
            {
                "status": "success",
                "message": "All ambulance attempts exhausted. Volunteer alerted.",
                "route": "volunteer",
                "volunteer": {
                    "id": nearest_volunteer.id,
                    "name": nearest_volunteer.name,
                    "phone": nearest_volunteer.contact,
                    "distance_km": volunteer_distance,
                },
            }
        )

    return Response({"status": "warning", "message": "Driver declined and no volunteer available"})


@api_view(["GET"])
def volunteer_requests(request):
    volunteer_id = request.query_params.get("volunteer_id")
    alerts = EmergencyAlert.objects.filter(status="volunteer_notified")
    if volunteer_id:
        alerts = alerts.filter(assigned_volunteer_id=volunteer_id)

    alert = alerts.order_by("-timestamp").first()
    if not alert:
        return Response({"message": "No requests"})

    return Response(
        {
            "id": alert.id,
            "name": alert.patient_name,
            "phone": alert.patient_phone,
            "lat": alert.latitude,
            "lng": alert.longitude,
        }
    )


def hospital_alerts(request):
    hosp_id = request.GET.get('hospital_id')
    try:
        hosp = hospital.objects.get(id=hosp_id)
        alert = EmergencyAlert.objects.filter(
            assigned_hospital=hosp,
            status='ambulance_accepted'
        ).order_by('-timestamp').first()
        if alert:
            return JsonResponse({
                'status':    'hospital_notified',
                'alert_id':  alert.id,
                'victim_lat':alert.latitude,
                'victim_lng':alert.longitude,
                'area':      f"{alert.latitude:.4f}, {alert.longitude:.4f}",
                'time':      alert.timestamp.strftime('%H:%M'),
            })
        return JsonResponse({'status': 'no_alert'})
    except hospital.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)


# ---------------------------------------------------------------------------
# Legacy-style realtime endpoints (JSON + csrf_exempt) requested by client app
# ---------------------------------------------------------------------------

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@csrf_exempt
def update_ambulance_location(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    amb_id = data.get("ambulance_id")
    lat = data.get("latitude")
    lng = data.get("longitude")

    if amb_id in (None, "") or lat in (None, "") or lng in (None, ""):
        return JsonResponse({"error": "ambulance_id, latitude and longitude are required"}, status=400)

    try:
        amb = ambulance.objects.get(id=amb_id)
        amb.latitude = float(lat)
        amb.longitude = float(lng)
        amb.save(update_fields=["latitude", "longitude"])
        return JsonResponse({"status": "ok"})
    except ambulance.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid coordinates"}, status=400)


@csrf_exempt
def trigger_sos(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    try:
        victim_lat = float(data.get("latitude"))
        victim_lng = float(data.get("longitude"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "latitude and longitude are required"}, status=400)

    victim_name = data.get("name", "Unknown")
    victim_phone = data.get("phone", "")

    alert = EmergencyAlert.objects.create(
        patient_name=victim_name,
        patient_phone=victim_phone,
        latitude=victim_lat,
        longitude=victim_lng,
        status="pending",
    )

    result = _dispatch_next_ambulance(alert)
    return JsonResponse(result)


@csrf_exempt
def ambulance_respond(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    alert_id = data.get("alert_id")
    amb_id = data.get("ambulance_id")
    accepted = data.get("accepted", False)

    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return JsonResponse({"error": "alert not found"}, status=404)

    if accepted:
        try:
            amb = ambulance.objects.get(id=amb_id)
        except ambulance.DoesNotExist:
            return JsonResponse({"error": "ambulance not found"}, status=404)

        # Backward-compatible: only toggle availability if field exists in schema.
        if any(field.name == "is_available" for field in ambulance._meta.fields):
            amb.is_available = False
            amb.save(update_fields=["is_available"])

        alert.assigned_driver = amb
        alert.status = "ambulance_accepted"
        alert.save(update_fields=["assigned_driver", "status"])

        _dispatch_next_hospital(alert)
        return JsonResponse(
            {
                "status": "accepted",
                "victim_lat": alert.latitude,
                "victim_lng": alert.longitude,
                "victim_name": alert.patient_name,
                "victim_phone": alert.patient_phone,
                "alert_id": alert.id,
            }
        )

    ids = list(alert.attempted_driver_ids or [])
    if amb_id not in ids:
        ids.append(amb_id)
    alert.attempted_driver_ids = ids
    alert.driver_attempt_count = len(ids)
    alert.save(update_fields=["attempted_driver_ids", "driver_attempt_count"])

    if alert.driver_attempt_count >= 3:
        _dispatch_volunteer(alert)
        return JsonResponse({"status": "dispatched_volunteer"})

    result = _dispatch_next_ambulance(alert)
    return JsonResponse(result)


@csrf_exempt
def hospital_respond(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    alert_id = data.get("alert_id")
    hosp_id = data.get("hospital_id")
    has_antiv = bool(data.get("antivenom", False))

    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if has_antiv:
        try:
            hosp = hospital.objects.get(id=hosp_id)
        except hospital.DoesNotExist:
            return JsonResponse({"error": "hospital not found"}, status=404)

        alert.assigned_hospital = hosp
        alert.status = "hospital_routed"
        alert.save(update_fields=["assigned_hospital", "status"])
        return JsonResponse(
            {
                "status": "confirmed",
                "hospital_lat": hosp.latitude,
                "hospital_lng": hosp.longitude,
                "hospital_name": hosp.name,
                "alert_id": alert.id,
            }
        )

    exclude_ids = []
    if hosp_id not in (None, ""):
        exclude_ids.append(hosp_id)
    result = _dispatch_next_hospital(alert, exclude_ids=exclude_ids)
    return JsonResponse(result)


def _dispatch_next_ambulance(alert):
    exclude_ids = list(alert.attempted_driver_ids or [])
    candidates = ambulance.objects.exclude(id__in=exclude_ids)

    if any(field.name == "is_available" for field in ambulance._meta.fields):
        candidates = candidates.filter(is_available=True)

    if not candidates.exists():
        alert.status = "pending"
        alert.save(update_fields=["status"])
        return {"status": "no_ambulance_available"}

    nearest = min(
        candidates,
        key=lambda a: haversine(alert.latitude, alert.longitude, a.latitude, a.longitude),
    )

    alert.assigned_driver = nearest
    alert.driver_notified_at = timezone.now()
    alert.status = "ambulance_notified"
    alert.save(update_fields=["assigned_driver", "driver_notified_at", "status"])

    return {
        "status": "ambulance_notified",
        "ambulance_id": nearest.id,
        "alert_id": alert.id,
        "victim_lat": alert.latitude,
        "victim_lng": alert.longitude,
        "victim_name": alert.patient_name,
    }


def _dispatch_next_hospital(alert, exclude_ids=None):
    exclude_ids = list(exclude_ids or [])
    candidates = hospital.objects.exclude(id__in=exclude_ids)

    if not candidates.exists():
        return {"status": "no_hospital_available"}

    nearest = min(
        candidates,
        key=lambda h: haversine(alert.latitude, alert.longitude, h.latitude, h.longitude),
    )

    alert.assigned_hospital = nearest
    alert.status = "hospital_routed"
    alert.save(update_fields=["assigned_hospital", "status"])

    return {
        "status": "hospital_notified",
        "hospital_id": nearest.id,
        "hospital_name": nearest.name,
        "alert_id": alert.id,
    }


def _dispatch_volunteer(alert):
    candidates = volunteer.objects.all()
    if not candidates.exists():
        alert.status = "pending"
        alert.save(update_fields=["status"])
        return

    nearest = min(
        candidates,
        key=lambda v: haversine(alert.latitude, alert.longitude, v.latitude, v.longitude),
    )

    alert.assigned_volunteer = nearest
    alert.status = "volunteer_notified"
    alert.save(update_fields=["assigned_volunteer", "status"])