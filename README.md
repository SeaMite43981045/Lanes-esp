# Lanes – Lightweight Async Web Framework for MicroPython

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MicroPython](https://img.shields.io/badge/MicroPython-2C3E50?logo=micropython)](https://micropython.org/)
[![ESP32](https://img.shields.io/badge/ESP32-Enabled-brightgreen)](https://www.espressif.com/)

**Lanes** is a lightweight, asynchronous web framework for **MicroPython**, designed to run efficiently on resource-constrained devices like ESP32, ESP8266, and RP2040. It provides routing, middleware, blueprints, static file serving, cookie handling, and JSON support – all in a familiar Flask-like syntax.

> **Version**: 1.0.1-pre
> **Status**: Stable for development / Experimental on some boards

---

## ✨ Features

- 🌐 **Async from the ground up** – Built on `asyncio` for concurrent request handling.
- 🧩 **Blueprint support** – Modularise your application.
- ⚙️ **Middleware support** – Run code before each request.
- 🗂️ **Static file serving** – Serve CSS, JS, images, etc.
- 📍 **Dynamic routing** – Extract URL parameters (`/user/:id`).
- 🍪 **Cookie handling** – Set and read cookies easily.
- 📦 **JSON auto‑serialisation** – Return `dict` / `list` as JSON.
- 📝 **Configurable logging** – DEBUG, INFO, WARN, ERROR, FATAL.
- 🧪 **Error handlers** (soon to be fully functional).
- 🚀 **Tiny memory footprint** – Suitable for ESP32 with ~300KB free heap.

---

## 📦 Installation

1. **Copy `lanes.py`** to your MicroPython device (e.g., via `ampy`, `mpremote`, or WebREPL).
2. **No additional dependencies** – uses only built-in modules: `asyncio`, `json`, `os`, `time`.

```bash
# Example using mpremote
mpremote cp lanes.py :/lib/lanes.py