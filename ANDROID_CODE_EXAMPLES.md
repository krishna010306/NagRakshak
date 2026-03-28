# ANDROID IMPLEMENTATION EXAMPLES

## METHOD 1: Using RETROFIT (Recommended - Modern Android)

### Step 1: Install Retrofit Dependency
```gradle
dependencies {
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.google.code.gson:gson:2.10.1'
}
```

### Step 2: Create Response Models

**User.java**
```java
public class User {
    public int id;
    public String name;
    public String phone;
    public String contact;
    public String email;
    public String role;
    public double latitude;
    public double longitude;
    public String eme_contact;
}
```

**ApiResponse.java**
```java
public class ApiResponse<T> {
    public String status;
    public String message;
    public T data;
    public T user;
    public T result;
}
```

**Alert.java**
```java
public class Alert {
    public int id;
    public String name;
    public String patient_name;
    public String phone;
    public String patient_phone;
    public double lat;
    public double lng;
    public double latitude;
    public double longitude;
    public String snake_type;
    public String vehicle;
    public int alert_id;
    public String status;
    public Hospital hospital;
    public AmbulanceDriver ambulance_driver;
    public List<String> first_aid;
}
```

### Step 3: Create API Interface

**ApiService.java**
```java
import retrofit2.Call;
import retrofit2.http.*;

public interface ApiService {
    
    // User Endpoints
    @POST("signup/")
    Call<ApiResponse<User>> register(@Body User user);
    
    @POST("login/")
    Call<ApiResponse<User>> login(@Body LoginRequest loginRequest);
    
    @GET("hospitals/")
    Call<List<Hospital>> getHospitals();
    
    @POST("nearest/")
    Call<Hospital> getNearestHospital(@Body LocationRequest locationRequest);
    
    // SOS Emergency
    @POST("sos/")
    Call<ApiResponse<Alert>> sendSOS(@Body SOSRequest sosRequest);
    
    // Driver Endpoints
    @GET("driver-requests/")
    Call<Alert> getDriverRequests(@Query("driver_id") int driverId);
    
    @GET("driver-requests/")
    Call<Alert> getDriverRequestsByPhone(@Query("phone") String phone);
    
    @POST("accept/")
    Call<ApiResponse<Alert>> acceptAlert(@Body AcceptRequest acceptRequest);
    
    // Volunteer Endpoints
    @GET("volunteer/")
    Call<Alert> getVolunteerRequests(@Query("volunteer_id") int volunteerId);
    
    // Hospital Endpoints
    @GET("hospital/")
    Call<List<Alert>> getHospitalAlerts();
}
```

### Step 4: Create Request Models

**LoginRequest.java**
```java
public class LoginRequest {
    public String email;
    public String password;
    
    public LoginRequest(String email, String password) {
        this.email = email;
        this.password = password;
    }
}
```

**SOSRequest.java**
```java
public class SOSRequest {
    public String name;
    public String phone;
    public String snake_type;
    public String vehicle;
    public double lat;
    public double lng;
    
    public SOSRequest(String name, String phone, String snakeType, 
                      String vehicle, double lat, double lng) {
        this.name = name;
        this.phone = phone;
        this.snake_type = snakeType;
        this.vehicle = vehicle;
        this.lat = lat;
        this.lng = lng;
    }
}
```

**AcceptRequest.java**
```java
public class AcceptRequest {
    public int id;
    public boolean accepted;
    
    public AcceptRequest(int id, boolean accepted) {
        this.id = id;
        this.accepted = accepted;
    }
}
```

### Step 5: Create Retrofit Client

**RetrofitClient.java**
```java
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class RetrofitClient {
    private static Retrofit retrofit = null;
    
    public static Retrofit getClient(String baseUrl) {
        if (retrofit == null) {
            retrofit = new Retrofit.Builder()
                    .baseUrl(baseUrl)
                    .addConverterFactory(GsonConverterFactory.create())
                    .build();
        }
        return retrofit;
    }
}
```

### Step 6: Use in Activity

**MainActivity.java** - Registration Example
```java
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MainActivity extends AppCompatActivity {
    private ApiService apiService;
    private EditText etName, etEmail, etPassword, etPhone;
    private double currentLat = 28.6139;
    private double currentLng = 77.2090;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Initialize Retrofit
        apiService = RetrofitClient.getClient("http://your-server/api/")
                                   .create(ApiService.class);
        
        // Get references to EditTexts
        etName = findViewById(R.id.et_name);
        etEmail = findViewById(R.id.et_email);
        etPassword = findViewById(R.id.et_password);
        etPhone = findViewById(R.id.et_phone);
        
        Button btnRegister = findViewById(R.id.btn_register);
        btnRegister.setOnClickListener(v -> registerUser());
    }
    
    private void registerUser() {
        String name = etName.getText().toString();
        String email = etEmail.getText().toString();
        String password = etPassword.getText().toString();
        String phone = etPhone.getText().toString();
        
        User user = new User();
        user.name = name;
        user.email = email;
        user.password = password;
        user.phone = phone;
        user.latitude = currentLat;
        user.longitude = currentLng;
        user.role = "victim";
        
        apiService.register(user).enqueue(new Callback<ApiResponse<User>>() {
            @Override
            public void onResponse(Call<ApiResponse<User>> call, 
                                 Response<ApiResponse<User>> response) {
                if (response.isSuccessful()) {
                    ApiResponse<User> apiResponse = response.body();
                    if ("success".equals(apiResponse.status)) {
                        Toast.makeText(MainActivity.this, 
                            "Registration Successful!", 
                            Toast.LENGTH_SHORT).show();
                        
                        User registeredUser = apiResponse.user;
                        int userId = registeredUser.id;
                        String userRole = registeredUser.role;
                        // Save to SharedPreferences or local database
                        saveUserData(userId, userRole);
                        
                        // Navigate to next screen
                        startActivity(new Intent(MainActivity.this, SosActivity.class));
                    }
                } else {
                    Toast.makeText(MainActivity.this, 
                        "Registration Failed: " + response.code(), 
                        Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<ApiResponse<User>> call, Throwable t) {
                Toast.makeText(MainActivity.this, 
                    "Network Error: " + t.getMessage(), 
                    Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void saveUserData(int userId, String role) {
        SharedPreferences sharedPref = getSharedPreferences("user_data", Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = sharedPref.edit();
        editor.putInt("user_id", userId);
        editor.putString("user_role", role);
        editor.apply();
    }
}
```

---

## METHOD 2: Using OkHttp + Custom JSON Parsing

### Step 1: Install OkHttp Dependency
```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.10.0'
    implementation 'org.json:json:20230227'
}
```

### Step 2: Create API Helper Class

**ApiHelper.java**
```java
import okhttp3.*;
import org.json.JSONObject;
import java.io.IOException;

public class ApiHelper {
    private static final String BASE_URL = "http://your-server/api/";
    private static final OkHttpClient client = new OkHttpClient();
    
    public static String sendPostRequest(String endpoint, JSONObject jsonBody) 
            throws IOException {
        String url = BASE_URL + endpoint;
        
        RequestBody body = RequestBody.create(
            jsonBody.toString(),
            MediaType.parse("application/json")
        );
        
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) 
                throw new IOException("Unexpected code " + response);
            
            return response.body().string();
        }
    }
    
    public static String sendGetRequest(String endpoint) 
            throws IOException {
        String url = BASE_URL + endpoint;
        
        Request request = new Request.Builder()
                .url(url)
                .get()
                .build();
        
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) 
                throw new IOException("Unexpected code " + response);
            
            return response.body().string();
        }
    }
}
```

### Step 3: Use in Activity

**LoginActivity.java**
```java
import android.os.AsyncTask;
import org.json.JSONObject;

public class LoginActivity extends AppCompatActivity {
    private EditText etEmail, etPassword;
    private ProgressBar progressBar;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        
        etEmail = findViewById(R.id.et_email);
        etPassword = findViewById(R.id.et_password);
        progressBar = findViewById(R.id.progress_bar);
        
        Button btnLogin = findViewById(R.id.btn_login);
        btnLogin.setOnClickListener(v -> performLogin());
    }
    
    private void performLogin() {
        String email = etEmail.getText().toString();
        String password = etPassword.getText().toString();
        
        if (email.isEmpty() || password.isEmpty()) {
            Toast.makeText(this, "Please enter email and password", 
                          Toast.LENGTH_SHORT).show();
            return;
        }
        
        new LoginTask().execute(email, password);
    }
    
    private class LoginTask extends AsyncTask<String, Void, String> {
        @Override
        protected void onPreExecute() {
            progressBar.setVisibility(View.VISIBLE);
        }
        
        @Override
        protected String doInBackground(String... params) {
            try {
                JSONObject loginJson = new JSONObject();
                loginJson.put("email", params[0]);
                loginJson.put("password", params[1]);
                
                return ApiHelper.sendPostRequest("login/", loginJson);
            } catch (Exception e) {
                return "error: " + e.getMessage();
            }
        }
        
        @Override
        protected void onPostExecute(String result) {
            progressBar.setVisibility(View.GONE);
            
            try {
                JSONObject response = new JSONObject(result);
                String status = response.getString("status");
                
                if ("success".equals(status)) {
                    JSONObject user = response.getJSONObject("user");
                    int userId = user.getInt("id");
                    String role = user.getString("role");
                    
                    // Save user data
                    SharedPreferences sharedPref = 
                        getSharedPreferences("user_data", Context.MODE_PRIVATE);
                    sharedPref.edit()
                        .putInt("user_id", userId)
                        .putString("user_role", role)
                        .apply();
                    
                    Toast.makeText(LoginActivity.this, "Login Successful!", 
                                  Toast.LENGTH_SHORT).show();
                    startActivity(new Intent(LoginActivity.this, 
                                            HomeActivity.class));
                    finish();
                } else {
                    String message = response.getString("message");
                    Toast.makeText(LoginActivity.this, message, 
                                  Toast.LENGTH_SHORT).show();
                }
            } catch (Exception e) {
                Toast.makeText(LoginActivity.this, 
                    "Error: " + e.getMessage(), 
                    Toast.LENGTH_SHORT).show();
            }
        }
    }
}
```

---

## METHOD 3: SOS Emergency Screen Implementation

**SosActivity.java**
```java
public class SosActivity extends AppCompatActivity {
    private EditText etPatientName, etPhone, etSnakeType;
    private CheckBox cbHasVehicle;
    private ApiService apiService;
    private LocationManager locationManager;
    private double currentLat, currentLng;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_sos);
        
        // Initialize views
        etPatientName = findViewById(R.id.et_patient_name);
        etPhone = findViewById(R.id.et_phone);
        etSnakeType = findViewById(R.id.et_snake_type);
        cbHasVehicle = findViewById(R.id.cb_has_vehicle);
        
        // Initialize Retrofit
        apiService = RetrofitClient.getClient("http://your-server/api/")
                                   .create(ApiService.class);
        
        // Get current location
        startLocationUpdates();
        
        // SOS Button
        Button btnSOS = findViewById(R.id.btn_sos);
        btnSOS.setOnClickListener(v -> sendSOS());
    }
    
    private void startLocationUpdates() {
        LocationManager locationManager = 
            (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        
        if (ActivityCompat.checkSelfPermission(this, 
                Manifest.permission.ACCESS_FINE_LOCATION) 
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION}, 100);
            return;
        }
        
        locationManager.requestLocationUpdates(
            LocationManager.GPS_PROVIDER,
            1000, // 1 second
            5,    // 5 meters
            location -> {
                currentLat = location.getLatitude();
                currentLng = location.getLongitude();
            }
        );
    }
    
    private void sendSOS() {
        String patientName = etPatientName.getText().toString();
        String phone = etPhone.getText().toString();
        String snakeType = etSnakeType.getText().toString();
        String vehicle = cbHasVehicle.isChecked() ? "yes" : "no";
        
        if (patientName.isEmpty() || phone.isEmpty()) {
            Toast.makeText(this, "Please enter patient name and phone", 
                          Toast.LENGTH_SHORT).show();
            return;
        }
        
        SOSRequest sosRequest = new SOSRequest(
            patientName,
            phone,
            snakeType.isEmpty() ? "unknown" : snakeType,
            vehicle,
            currentLat,
            currentLng
        );
        
        apiService.sendSOS(sosRequest).enqueue(
            new Callback<ApiResponse<Alert>>() {
                @Override
                public void onResponse(Call<ApiResponse<Alert>> call,
                                     Response<ApiResponse<Alert>> response) {
                    if (response.isSuccessful()) {
                        ApiResponse<Alert> apiResponse = response.body();
                        Alert alert = apiResponse.data;
                        
                        // Show first aid steps
                        showFirstAidDialog(alert.first_aid);
                        
                        // Navigate to tracking screen
                        Intent intent = new Intent(SosActivity.this, 
                                                  TrackingActivity.class);
                        intent.putExtra("alert_id", alert.alert_id);
                        intent.putExtra("route", alert.route);
                        startActivity(intent);
                    }
                }
                
                @Override
                public void onFailure(Call<ApiResponse<Alert>> call, 
                                    Throwable t) {
                    Toast.makeText(SosActivity.this, 
                        "Error: " + t.getMessage(), 
                        Toast.LENGTH_SHORT).show();
                }
            }
        );
    }
    
    private void showFirstAidDialog(List<String> firstAidSteps) {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("FIRST AID STEPS");
        
        StringBuilder steps = new StringBuilder();
        for (String step : firstAidSteps) {
            steps.append("• ").append(step).append("\n\n");
        }
        
        builder.setMessage(steps.toString());
        builder.setPositiveButton("OK", (dialog, which) -> dialog.dismiss());
        builder.show();
    }
}
```

---

## SHARED PREFERENCES HELPER

**UserPreferences.java**
```java
import android.content.Context;
import android.content.SharedPreferences;

public class UserPreferences {
    private static final String PREF_NAME = "user_data";
    private SharedPreferences sharedPreferences;
    
    public UserPreferences(Context context) {
        this.sharedPreferences = 
            context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }
    
    public void saveUser(int userId, String email, String role) {
        sharedPreferences.edit()
            .putInt("user_id", userId)
            .putString("user_email", email)
            .putString("user_role", role)
            .apply();
    }
    
    public int getUserId() {
        return sharedPreferences.getInt("user_id", -1);
    }
    
    public String getUserRole() {
        return sharedPreferences.getString("user_role", "");
    }
    
    public void clearUser() {
        sharedPreferences.edit().clear().apply();
    }
    
    public boolean isLoggedIn() {
        return getUserId() != -1;
    }
}
```

---

## COMMON MISTAKES TO AVOID

1. ❌ Forgetting to include GPS coordinates in requests
2. ❌ Not handling network errors gracefully
3. ❌ Storing passwords in plaintext (let Django hash them)
4. ❌ Not validating inputs before sending
5. ❌ Hardcoding server URL (use BuildConfig or config file)
6. ❌ Not requesting location permissions before using GPS
7. ❌ Ignoring response status field in JSON
8. ❌ Making network calls on main thread
9. ❌ Not parsing error messages from API
10. ❌ Forgetting to add INTERNET permission in AndroidManifest.xml

---

## REQUIRED PERMISSIONS (AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

