# Lanes

Lanes is a lightweight, high-performance, asynchronous web framework designed specifically for **MicroPython** (optimized for ESP32 and similar resource-constrained microcontrollers). Inspired by modern desktop frameworks like Flask and Sanic, Lanes brings an expressive, decorator-based routing system and standard HTTP abstractions to the embedded world.

**Current Version:** `1.1.0-pre`

---

## 🚀 Features

* **Asynchronous Core:** Built entirely on top of MicroPython's `asyncio` for non-blocking I/O operations.
* **Expressive Routing:** Supports explicit decorators (`@app.get`, `@app.post`, etc.) and dynamic URL path parameters (e.g., `/api/sensor/:id`).
* **Modular Infrastructure:** Partition your application logic easily using `Blueprint` modules.
* **Static File Serving:** Built-in streaming mechanism to serve asset files (CSS, JS, Images) straight from your device's filesystem (`os.path`).
* **Template Engine:** A built-in template renderer (`render_template`) supporting dynamic placeholder substitutions via `{{ keyword }}` syntax.
* **Middleware Hooks:** Intercept and process incoming queries globally or modularly using pre-request intercepts (`@app.before_request`).
* **Custom Error Handling:** Map custom fallback logic directly to specific HTTP error status codes (`4xx`, `5xx`) using `@app.error_handler(status)`.

---

## 🛠️ Quick Start

Here is a quick look at how easy it is to spin up a web server with Lanes on your microcontroller:

```python
import asyncio
from lanes import Lanes, render_template

app = Lanes()

# 1. Basic Plain Text Route
@app.get("/")
def index(req):
    return "Hello from Lanes!"

# 2. Dynamic Path Parameter Route
@app.get("/api/hardware/:pin")
def read_pin(req, pin):
    return {"pin_requested": pin, "status": "high"}

# 3. Handling POST with JSON Payloads
@app.post("/api/led/control")
def control_led(req):
    state = req.body.get("state", "off")
    # Add your hardware interaction logic here (e.g., machine.Pin)
    return {"success": True, "new_state": state}

# 4. Rendering HTML Templates
@app.get("/dashboard")
def view_dashboard(req):
    return render_template("templates/index.html", title="ESP32 Board", status="Active")

# 5. Starting the Server
if __name__ == "__main__":
    # Host defaults to 0.0.0.0 and port to 80
    app.run(host="0.0.0.0", port=80)
```

---

## 📁 Directory Structure Recommendation

To make full use of the built-in asset and template tools, we suggest organizing your MicroPython project as follows:

```text
├── main.py              # Server entry point
├── lanes.py             # Lanes core framework file
├── assets/              # Default static assets folder (CSS, JS, Icons)
│   ├── style.css
│   └── script.js
└── templates/           # HTML templates folder
    └── index.html
```

---

## 📖 Detailed Documentation (Wiki)

For deep-dive architectural tutorials, comprehensive API references, and code examples covering middleware, blueprints, and request/response lifecycles, please visit our official Wiki pages:

* 🌐 **GitHub Documentation:** [GitHub Wiki](https://github.com/SeaMite43981045/Lanes-esp/wiki)
* 🇨🇳 **Gitee Documentation (Mirror):** [Gitee Wiki](https://gitee.com/SeaMite43981045/Lanes-esp/wikis)

---

## 📄 License

This project is licensed under the **MIT License** - see below for details:

```text
MIT License

Copyright (c) 2026 SeaMite43981045

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.