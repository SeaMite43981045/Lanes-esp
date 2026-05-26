# 🚀 Lanes Framework Quickstart Guide

Welcome to **Lanes**! This is a lightweight, asynchronous web framework designed specifically for ESP32 and MicroPython environments. This guide will take you from scratch to building your first IoT web application step-by-step.

## 📋 Table of Contents

1. [Environment Setup](https://www.google.com/search?q=%231-environment-setup)
2. [Your First Hello World](https://www.google.com/search?q=%232-your-first-hello-world)
3. [Routing and HTTP Methods](https://www.google.com/search?q=%233-routing-and-http-methods)
4. [Parsing Requests (Request Object)](https://www.google.com/search?q=%234-parsing-requests-request-object)
5. [Building Responses (Response Object)](https://www.google.com/search?q=%235-building-responses-response-object)
6. [Blueprint Modularity](https://www.google.com/search?q=%236-blueprint-modularity)
7. [Middleware Interceptors](https://www.google.com/search?q=%237-middleware-interceptors)
8. [Static File Hosting](https://www.google.com/search?q=%238-static-file-hosting)

---

## 1. Environment Setup

Before writing any code, ensure you have the following ready:

* A development board flashed with **MicroPython** firmware (ESP32 is highly recommended).
* The `lanes.py` file uploaded to the root directory or the `/lib` directory of your board.

> **⚠️ Important Note:** The Lanes framework does not manage Wi-Fi connections. Before starting the server, make sure your board is successfully connected to a local network (STA mode) or has its access point enabled (AP mode).

---

## 2. Your First Hello World

Create a `main.py` file and write your very first Lanes application:

```python
# main.py
import network
import time
from lanes import Lanes

# 1. Simple Wi-Fi connection logic (Example)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('YOUR_WIFI_SSID', 'YOUR_WIFI_PASSWORD')
while not wlan.isconnected():
    time.sleep(1)
print('Network connected:', wlan.ifconfig())

# 2. Initialize the Lanes framework
app = Lanes(log_level=1) # Enable INFO level logging

# 3. Register a route
@app.get("/")
def index(req):
    return "Hello, MicroPython World!"

# 4. Start the server
if __name__ == "__main__":
    # Listens on 0.0.0.0:80 by default
    app.run(host="0.0.0.0", port=80)

```

Upload and run `main.py`. Access your board's IP address in a web browser, and you will see `Hello, MicroPython World!`.

---

## 3. Routing and HTTP Methods

Lanes supports standard HTTP method registration and dynamic route parameters.

### Basic Method Registration

You can use decorators to quickly register specific HTTP methods:

```python
@app.get("/api/data")
def get_data(req):
    return {"message": "This is a GET request"}

@app.post("/api/data")
def create_data(req):
    return {"message": "This is a POST request"}
    
# @app.put() and @app.delete() are also supported

```

### Dynamic Path Parameters

You can extract variables from the URL using the `:parameter_name` syntax. The framework will automatically pass them as keyword arguments to your callback function:

```python
@app.get("/users/:id")
def get_user(req, id):
    return {"user_id": id, "name": f"User_{id}"}

@app.get("/device/:type/:action")
def control_device(req, type, action):
    return {"device_type": type, "action": action}

```

---

## 4. Parsing Requests (Request Object)

The first parameter of every route callback function is the `Request` object, which contains all the information sent by the client.

| Attribute | Description | Example |
| --- | --- | --- |
| `req.method` | The HTTP method (Uppercase string) | `"GET"`, `"POST"` |
| `req.path` | The requested path | `"/api/status"` |
| `req.headers` | Request headers (Dictionary, lowercase keys) | `{"content-type": "application/json"}` |
| `req.params` | URL Query parameters (Dictionary) | `?name=esp32` -> `{"name": "esp32"}` |
| `req.body` | Parsed JSON payload | `{"switch": "on"}` |
| `req.cookies` | Parsed Cookies (Dictionary) | `{"session": "xyz123"}` |

**Example of handling a POST request and Query parameters:**

```python
@app.post("/api/config")
def update_config(req):
    # Read parameters from /api/config?force=true
    is_force = req.params.get("force", "false")
    
    # Read the JSON payload sent by the client
    payload = req.body
    
    return {
        "status": "success",
        "received_data": payload,
        "forced": is_force
    }

```

---

## 5. Building Responses (Response Object)

Lanes provides highly flexible ways to return responses. You can return raw data directly (the framework will intelligently infer the `Content-Type`), or use the `Response` object for fine-grained control.

### Quick Returns

* **Return a Dictionary/List**: Automatically converted to JSON with a default `200` status code.
* **Return a String**: Automatically identifies if it is HTML (starts with `<html>` or `<!doctype`), otherwise returns plain text.
* **Return a Tuple**: Allows you to specify both the data and the status code simultaneously, e.g., `(data, status_code)`.

```python
@app.get("/status")
def status(req):
    # Quick return of JSON and a 404 status code
    return {"error": "Device offline"}, 404

```

### Using the Response Object (Advanced)

When you need to set Cookies or strictly control the response, use the `Response` class:

```python
from lanes import Response

@app.post("/login")
def login(req):
    if req.body.get("pwd") == "123456":
        res = Response({"msg": "Login successful"}, 200)
        # Set a Cookie
        res.set_cookie("token", "admin_token", max_age=3600, httponly=True)
        return res
    else:
        return {"msg": "Incorrect password"}, 401

```

---

## 6. Blueprint Modularity

To prevent your `main.py` from becoming too bloated, you can use a `Blueprint` to split your APIs into different files.

**Step 1: Create a blueprint module (e.g., `routes/api.py`)**

```python
from lanes import Blueprint

api_bp = Blueprint(url_prefix="/api/v1")

@api_bp.get("/info")
def get_info(req):
    return {"version": "1.0", "device": "ESP32"}

```

**Step 2: Register the blueprint in your main application**

```python
from lanes import Lanes
from routes.api import api_bp

app = Lanes()
app.register_blueprint(api_bp)

# You can now access this route via /api/v1/info

```

---

## 7. Middleware Interceptors

Middleware allows you to execute unified logic (such as permission checks or logging) before the request actually reaches your route function.

```python
@app.before_request()
def auth_middleware(req):
    # Assume all paths starting with /admin require Cookie validation
    if req.path.startswith("/admin"):
        token = req.cookies.get("token")
        if token != "admin_token":
            # Note: In the current framework design, raising an exception 
            # in middleware will return a generic 500 Internal Error.
            raise Exception("Unauthorized Access")

```

---

## 8. Static File Hosting

In IoT development, you often need a web dashboard. Lanes supports directly mapping a folder on the board's internal Flash to a network path and serves the files via chunked streaming (to prevent out-of-memory errors).

```python
# Mount the local "./web" directory to the "/dashboard" URL prefix
app.static("/dashboard", "./web")

```

**Example File Structure:**

```text
/ (Board Root)
├── lanes.py
├── main.py
└── web/
    ├── index.html
    ├── style.css
    └── app.js

```

Accessing `http://<BOARD_IP>/dashboard/index.html` will seamlessly load the web page. The framework automatically handles common MIME types like `text/html`, `text/css`, and `application/javascript`.</BOARD_IP></BOARD_IP>