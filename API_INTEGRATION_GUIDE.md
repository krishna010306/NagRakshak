# ANDROID APK TO DJANGO API INTEGRATION GUIDE

## Server Connection Details
- **Base URL**: `http://localhost:8000/api/` (or your server IP/domain)
- **Content-Type**: `application/json` for all requests
- **Method**: POST for data submission, GET for data retrieval

---

## 1. USER REGISTRATION / SIGNUP

### Endpoint
```
POST /api/signup/
or
POST /api/register/
or
POST /api/user-create/
```

### Android TextBox Field Names
```java
EditText etName = findViewById(R.id.name);
EditText etEmail = findViewById(R.id.email);
EditText etPassword = findViewById(R.id.password);
EditText etPhone = findViewById(R.id.phone);  // or contact
EditText etRole = findViewById(R.id.role);     // Optional: victim/driver/volunteer/hospital
EditText etEmergencyContact = findViewById(R.id.eme_contact);
// Location (from GPS)
Double latitude = getLatitude();
Double longitude = getLongitude();
```

### Request JSON
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password123",
  "phone": "9876543210",
  "contact": "9876543210",
  "role": "victim",
  "eme_contact": "9876543211",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "lat": 28.6139,
  "lng": 77.2090
}
```

### Response (201 Created / 200 OK)
```json
{
  "status": "success",
  "created": true,
  "role": "victim",
  "user": {
    "id": 1,
    "name": "John Doe",
    "phone": "9876543210",
    "contact": "9876543210",
    "email": "john@example.com",
    "role": "victim",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "eme_contact": "9876543211"
  }
}
```

### Error Response (400)
```json
{
  "status": "error",
  "message": "email and password are required"
}
```

---

## 2. USER LOGIN

### Endpoint
```
POST /api/login/
```

### Android TextBox Field Names
```java
EditText etEmail = findViewById(R.id.email);
EditText etPassword = findViewById(R.id.password);
```

### Request JSON
```json
{
  "email": "john@example.com",
  "password": "secure_password123"
}
```

### Response (200 OK)
```json
{
  "status": "success",
  "message": "Login successful",
  "next_screen": "sos",
  "role": "victim",
  "user": {
    "id": 1,
    "name": "John Doe",
    "phone": "9876543210",
    "email": "john@example.com",
    "role": "victim",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "eme_contact": "9876543211"
  }
}
```

---

## 3. EMERGENCY SOS ALERT

### Endpoint
```
POST /api/sos/
or
POST /api/alert/
or
POST /api/send_alert/
or
POST /api/ambulance-request/
or
POST /api/smart/
```

### Android TextBox Field Names
```java
EditText etPatientName = findViewById(R.id.name);
EditText etPhone = findViewById(R.id.phone);
EditText etSnakeType = findViewById(R.id.snake_type);  // Optional
CheckBox cbHasVehicle = findViewById(R.id.has_vehicle);
Double latitude = getLatitude();
Double longitude = getLongitude();
```

### Request JSON
```json
{
  "name": "Patient Name",
  "phone": "9876543210",
  "contact": "9876543210",
  "email": "john@example.com",
  "snake_type": "cobra",
  "vehicle": "yes",
  "lat": 28.6139,
  "lng": 77.2090,
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

### Response (200 OK)
```json
{
  "status": "success",
  "alert_id": 5,
  "route": "ambulance",
  "message": "Ambulance alerted. If not accepted in 5 minutes, system tries next driver (max 3), then volunteer.",
  "first_aid": [
    "Keep the patient calm and still.",
    "Remove rings, bangles, and tight clothing near bite area.",
    "Do not cut, suck, or apply ice on the bite.",
    "Keep bitten limb below heart level and avoid walking.",
    "Reach anti-venom capable hospital immediately."
  ],
  "hospital_alerted": true,
  "hospital": {
    "id": 2,
    "name": "Apollo Hospital Delhi",
    "phone": "1140161000"
  },
  "ambulance_driver": {
    "id": 1,
    "name": "Raj Kumar",
    "phone": "9876543200",
    "distance_km": 2.5
  },
  "attempt": 1,
  "wait_time_minutes": 5
}
```

---

## 4. ACCEPT/REJECT AMBULANCE REQUEST (Driver Response)

### Endpoint
```
POST /api/accept/
```

### Android TextBox Field Names
```java
EditText etAlertId = findViewById(R.id.alert_id);
CheckBox cbAccepted = findViewById(R.id.accepted);
```

### Request JSON
```json
{
  "id": 5,
  "accepted": true
}
```

### Response - Accept (200 OK)
```json
{
  "status": "success",
  "message": "Accepted. Hospital has been notified that victim is coming.",
  "alert_id": 5,
  "patient": {
    "name": "Patient Name",
    "phone": "9876543210",
    "lat": 28.6139,
    "lng": 77.2090
  },
  "hospital": {
    "id": 2,
    "name": "Apollo Hospital Delhi",
    "phone": "1140161000"
  },
  "next_screen": "victim_location_and_navigation"
}
```

### Response - Reject (200 OK)
```json
{
  "status": "success",
  "message": "Driver declined. Request moved to next nearest ambulance driver.",
  "route": "ambulance",
  "attempt": 2,
  "ambulance_driver": {
    "id": 2,
    "name": "Priya Singh",
    "phone": "9876543201",
    "distance_km": 3.2
  }
}
```

---

## 5. GET ALL HOSPITALS

### Endpoint
```
GET /api/hospitals/
```

### Request
No parameters needed.

### Response (200 OK)
```json
[
  {
    "id": 1,
    "name": "AIIMS Delhi",
    "lat": 28.5930,
    "lng": 77.2197,
    "phone": "1126588500",
    "has_antivenom": true
  },
  {
    "id": 2,
    "name": "Apollo Hospital Delhi",
    "lat": 28.5244,
    "lng": 77.1855,
    "phone": "1140161000",
    "has_antivenom": true
  }
]
```

---

## 6. GET NEAREST HOSPITAL

### Endpoint
```
POST /api/nearest/
```

### Android TextBox Field Names
```java
Double latitude = getLatitude();
Double longitude = getLongitude();
```

### Request JSON
```json
{
  "user_id": 1,
  "lat": 28.6139,
  "lng": 77.2090,
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

### Response (200 OK)
```json
{
  "id": 1,
  "name": "AIIMS Delhi",
  "lat": 28.5930,
  "lng": 77.2197,
  "phone": "1126588500",
  "distance_km": 5.2,
  "has_antivenom": true
}
```

---

## 7. GET AMBULANCE DRIVER REQUESTS

### Endpoint
```
GET /api/driver-requests/
or
POST /api/ambulance-request/
```

### Request Parameters
```
?driver_id=1
or
?phone=9876543200
```

### Response (200 OK)
```json
{
  "id": 5,
  "name": "Patient Name",
  "phone": "9876543210",
  "victim_phone": "9876543210",
  "lat": 28.6139,
  "lng": 77.2090,
  "attempt": 1,
  "response_deadline": "2026-03-29T18:45:00Z",
  "hospital": {
    "name": "Apollo Hospital Delhi",
    "phone": "1140161000"
  }
}
```

---

## 8. GET VOLUNTEER REQUESTS

### Endpoint
```
GET /api/volunteer/
```

### Request Parameters
```
?volunteer_id=1
```

### Response (200 OK)
```json
{
  "id": 5,
  "name": "Patient Name",
  "phone": "9876543210",
  "lat": 28.6139,
  "lng": 77.2090
}
```

---

## 9. GET HOSPITAL ALERTS

### Endpoint
```
GET /api/hospital/
```

### Response (200 OK)
```json
[
  {
    "alert_id": 5,
    "status": "ambulance_accepted",
    "patient_name": "Patient Name",
    "patient_phone": "9876543210",
    "lat": 28.6139,
    "lng": 77.2090,
    "hospital": {
      "name": "Apollo Hospital Delhi",
      "phone": "1140161000"
    }
  }
]
```

---

## KEY FIELD NAMES TO REMEMBER

### User Fields
- `name` - Full name
- `email` - Email address (unique)
- `password` - Password (will be hashed)
- `phone` / `contact` - Phone number (10+ digits)
- `role` - One of: `victim`, `driver`, `volunteer`, `hospital`
- `eme_contact` - Emergency contact
- `latitude` / `lat` - GPS latitude
- `longitude` / `lng` - GPS longitude
- `user_id` - For identifying user in requests

### Alert Fields
- `name` - Patient name
- `phone` / `contact` - Patient phone
- `snake_type` - Type of snake
- `vehicle` - Yes/No (does patient have vehicle to reach hospital)
- `lat` / `latitude` - Patient location latitude
- `lng` / `longitude` - Patient location longitude

### Driver/Ambulance Fields
- `driver_id` - Driver ID
- `id` - Alert ID or Resource ID
- `accepted` - true/false for accepting alert

### Hospital/Location Fields
- `latitude` / `lat` - Location latitude
- `longitude` / `lng` - Location longitude
- `distance_km` - Distance in kilometers
- `has_antivenom` - Whether hospital has antivenom

---

## ANDROID CODE EXAMPLE

### Build JSON Request
```java
JSONObject json = new JSONObject();
try {
    json.put("name", etName.getText().toString());
    json.put("email", etEmail.getText().toString());
    json.put("password", etPassword.getText().toString());
    json.put("phone", etPhone.getText().toString());
    json.put("lat", latitude);
    json.put("lng", longitude);
} catch (JSONException e) {
    e.printStackTrace();
}
```

### Make POST Request (Volley Library)
```java
String url = "http://localhost:8000/api/signup/";
RequestQueue queue = Volley.newRequestQueue(this);

JsonObjectRequest jsonRequest = new JsonObjectRequest(
    Request.Method.POST,
    url,
    json,
    new Response.Listener<JSONObject>() {
        @Override
        public void onResponse(JSONObject response) {
            Toast.makeText(MainActivity.this, 
                "Registration Successful", 
                Toast.LENGTH_SHORT).show();
        }
    },
    new Response.ErrorListener() {
        @Override
        public void onErrorResponse(VolleyError error) {
            Toast.makeText(MainActivity.this, 
                "Error: " + error.getMessage(), 
                Toast.LENGTH_SHORT).show();
        }
    }
);

queue.add(jsonRequest);
```

### Make GET Request
```java
String url = "http://localhost:8000/api/hospitals/";

StringRequest stringRequest = new StringRequest(
    Request.Method.GET,
    url,
    new Response.Listener<String>() {
        @Override
        public void onResponse(String response) {
            try {
                JSONArray hospitals = new JSONArray(response);
                // Parse hospitals array
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
    },
    new Response.ErrorListener() {
        @Override
        public void onErrorResponse(VolleyError error) {
            Toast.makeText(MainActivity.this, 
                "Error loading hospitals", 
                Toast.LENGTH_SHORT).show();
        }
    }
);

RequestQueue queue = Volley.newRequestQueue(this);
queue.add(stringRequest);
```

---

## ERROR CODES

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (missing/invalid fields) |
| 401 | Unauthorized (wrong password) |
| 404 | Not Found |
| 500 | Server Error |

---

## IMPORTANT NOTES

1. **Always include GPS coordinates** (lat/lng or latitude/longitude) in SOS and registration
2. **Phone validation**: Must be at least 10 digits
3. **Coordinate validation**: Latitude must be -90 to 90, Longitude must be -180 to 180
4. **Password hashing**: Never store plaintext passwords. Django handles this automatically
5. **Role values**: Only accept exact values: `victim`, `driver`, `volunteer`, `hospital`
6. **Vehicle field**: Accept yes/no, true/false, 1/0
7. **Error handling**: Always check the `status` field in response
8. **Timeout**: Drivers have 5 minutes to respond to alerts
9. **Max attempts**: System tries 3 drivers before escalating to volunteer
10. **Email unique**: Each email can only register once

---

## FLOW DIAGRAMS

### User Registration + SOS Alert Flow
```
APK: Register User
  → POST /api/signup/
  → Backend: Create User
  → Response: User ID, Role

APK: Send SOS
  → POST /api/sos/
  → Backend: Find nearest hospital → ambulance → volunteer
  → Response: Alert details, Helper assignments

APK: Display helper info & first aid steps
```

### Driver Flow
```
APK (Driver): Get Current Requests
  → GET /api/driver-requests/
  → Response: Current alert (if any)

APK: Show patient location, hospital, directions
APK: Accept/Decline button
  → POST /api/accept/ (with accepted: true/false)
  → Backend: Update status
  → Response: Instructions (go to hospital or next driver assigned)
```

