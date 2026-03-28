# QUICK REFERENCE - APK FIELD NAMES & API ENDPOINTS

## ALL ENDPOINTS & THEIR FIELD NAMES

### 1. SIGNUP/REGISTER
**URL:** `POST http://your-server/api/signup/`  
**Fields to send:**
```
name, email, password, phone, latitude, longitude
OPTIONAL: role, eme_contact
```

### 2. LOGIN  
**URL:** `POST http://your-server/api/login/`  
**Fields to send:**
```
email, password
```

### 3. EMERGENCY SOS
**URL:** `POST http://your-server/api/sos/`  
**Fields to send:**
```
name (patient name)
phone (patient phone)
lat, lng (GPS coordinates)
OPTIONAL: snake_type, vehicle (yes/no)
```

### 4. GET HOSPITALS
**URL:** `GET http://your-server/api/hospitals/`  
**Fields to send:** None (just call it)

### 5. GET NEAREST HOSPITAL
**URL:** `POST http://your-server/api/nearest/`  
**Fields to send:**
```
lat, lng OR latitude, longitude
OPTIONAL: user_id (or email/phone to identify user)
```

### 6. DRIVER - GET CURRENT ALERT
**URL:** `GET http://your-server/api/driver-requests/?driver_id=YOUR_ID`  
**OR:** `GET http://your-server/api/driver-requests/?phone=YOURPHONE`  
**Fields:** None (pass as URL parameters)

### 7. DRIVER - ACCEPT/REJECT ALERT
**URL:** `POST http://your-server/api/accept/`  
**Fields to send:**
```
id (alert ID)
accepted (true or false)
```

### 8. VOLUNTEER - GET CURRENT ALERT
**URL:** `GET http://your-server/api/volunteer/?volunteer_id=YOUR_ID`  
**Fields:** None

### 9. HOSPITAL - GET ALERTS
**URL:** `GET http://your-server/api/hospital/`  
**Fields:** None

---

## DATABASE FIELD NAMES (What to store in your app)

### User Table Fields
```
id (auto, don't send)
name (TEXT)
email (TEXT, unique)
password (TEXT, will be hashed)
phone / contact (TEXT, 10+ digits)
role (TEXT: victim/driver/volunteer/hospital)
latitude (DECIMAL)
longitude (DECIMAL)
eme_contact (TEXT, emergency contact)
```

### Alert Table Fields
```
id (auto, don't send)
patient_name (TEXT)
patient_phone (TEXT)
latitude (DECIMAL)
longitude (DECIMAL)
snake_type (TEXT, optional)
has_vehicle (BOOLEAN: yes/no)
status (TEXT: pending/hospital_routed/ambulance_notified/ambulance_accepted/volunteer_notified/completed)
```

### Hospital Fields
```
id (auto)
name (TEXT)
phone (TEXT)
latitude (DECIMAL)
longitude (DECIMAL)
has_antivenom (BOOLEAN)
```

### Ambulance/Driver Fields
```
id (auto)
name (TEXT)
phone (TEXT)
latitude (DECIMAL, current location)
longitude (DECIMAL, current location)
```

### Volunteer Fields
Same as Ambulance

---

## RESPONSE FORMAT

### ALL Successful Responses Have:
```json
{
  "status": "success",
  "data": { ... }
}
```

### ALL Error Responses Have:
```json
{
  "status": "error",
  "message": "A human-readable error message"
}
```

---

## ANDROID TEXTBOX/FIELD SETUP EXAMPLE

```java
// Registration Screen TextBoxes
EditText et_name = findViewById(R.id.name);
EditText et_email = findViewById(R.id.email);
EditText et_password = findViewById(R.id.password);
EditText et_phone = findViewById(R.id.phone);  // or contact
Spinner sp_role = findViewById(R.id.role);     // dropdown: victim/driver/volunteer
EditText et_emerg_contact = findViewById(R.id.emergency_contact);

// SOS Screen TextBoxes
EditText et_patient_name = findViewById(R.id.patient_name);
EditText et_patient_phone = findViewById(R.id.patient_phone);
EditText et_snake_type = findViewById(R.id.snake_type);
CheckBox cb_has_vehicle = findViewById(R.id.has_vehicle);

// GPS Location (from LocationManager or FusedLocationProvider)
double current_lat = location.getLatitude();
double current_lng = location.getLongitude();

// Button clicks
Button btn_register = findViewById(R.id.register_button);
Button btn_login = findViewById(R.id.login_button);
Button btn_sos = findViewById(R.id.sos_button);
Button btn_accept = findViewById(R.id.accept_button);
Button btn_decline = findViewById(R.id.decline_button);
```

---

## JSON REQUEST TEMPLATES (Copy-Paste Ready)

### Template 1: Register
```json
{
  "name": "User Name",
  "email": "user@email.com",
  "password": "password123",
  "phone": "9876543210",
  "role": "victim",
  "latitude": 28.6,
  "longitude": 77.2,
  "eme_contact": "9876543211"
}
```

### Template 2: Login
```json
{
  "email": "user@email.com",
  "password": "password123"
}
```

### Template 3: SOS Alert
```json
{
  "name": "Patient Name",
  "phone": "9876543210",
  "snake_type": "cobra",
  "vehicle": "no",
  "lat": 28.6,
  "lng": 77.2
}
```

### Template 4: Accept Alert (Driver)
```json
{
  "id": 5,
  "accepted": true
}
```

### Template 5: Reject Alert (Driver)  
```json
{
  "id": 5,
  "accepted": false
}
```

---

## RESPONSE TEMPLATES

### Successful Registration
```json
{
  "status": "success",
  "user": {
    "id": 1,
    "name": "User Name",
    "phone": "9876543210",
    "email": "user@email.com",
    "role": "victim",
    "latitude": 28.6,
    "longitude": 77.2
  }
}
```

### Successful SOS Alert
```json
{
  "status": "success",
  "alert_id": 5,
  "route": "ambulance",
  "ambulance_driver": {
    "id": 1,
    "name": "Driver Name",
    "phone": "9876543200",
    "distance_km": 2.5
  },
  "hospital": {
    "id": 2,
    "name": "Hospital Name",
    "phone": "1140161000"
  },
  "first_aid": [
    "Step 1...",
    "Step 2..."
  ]
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Phone number must be at least 10 digits"
}
```

---

## VALIDATION RULES FOR YOUR APK

| Field | Rule | Example |
|-------|------|---------|
| name | Required, min 1 char | "John Doe" |
| email | Required, valid format | "john@example.com" |
| password | Required, min 6 chars | "password123" |
| phone | Required, 10+ digits | "9876543210" |
| role | Only: victim/driver/volunteer/hospital | "victim" |
| latitude | -90 to 90 | 28.6139 |
| longitude | -180 to 180 | 77.2090 |
| vehicle | yes/no or true/false | "yes" |

---

## CHECKLIST FOR APK DEVELOPMENT

- [ ] Get GPS coordinates (use FusedLocationProvider or LocationManager)
- [ ] Create registration screen with all fields
- [ ] Create login screen (email + password)
- [ ] Create SOS emergency screen (name, phone, location, snake type)
- [ ] Parse responses and extract user ID for future requests
- [ ] Display hospitals list fetched from API
- [ ] Show driver requests (for ambulance drivers)
- [ ] Accept/decline button for drivers
- [ ] Show volunteer requests (for volunteers)
- [ ] Show hospital alerts (for hospitals)
- [ ] Implement error handling (check status field)
- [ ] Add loading indicators during API calls
- [ ] Handle no-internet scenarios gracefully
- [ ] Format timestamps correctly in responses
- [ ] Test all endpoints before release

---

## QUICK API CALL PATTERN IN ANDROID

All API calls follow this pattern:

```java
// 1. Prepare JSON
JSONObject params = new JSONObject();
params.put("field_name", value);

// 2. Choose method
String method = "POST"; // or "GET"

// 3. Make request
JsonObjectRequest request = new JsonObjectRequest(
    Request.Method.POST,
    "http://server/api/endpoint/",
    params,
    response -> {
        String status = response.getString("status");
        if ("success".equals(status)) {
            // Handle success
        } else {
            // Handle error
        }
    },
    error -> {
        // Handle network/server error
    }
);

queue.add(request);
```

