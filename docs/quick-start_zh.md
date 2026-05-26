# 🚀 Lanes 框架快速上手指南 (Quickstart)

欢迎使用 **Lanes**！这是一个专为 ESP32 和 MicroPython 环境设计的轻量级、异步 Web 框架。本指南将带你从零开始，一步步构建你的物联网 Web 应用。

## 📋 目录

1. [环境准备](https://www.google.com/search?q=%231-%E7%8E%AF%E5%A2%83%E5%87%86%E5%A4%87)
2. [第一个 Hello World](https://www.google.com/search?q=%232-%E7%AC%AC%E4%B8%80%E4%B8%AA-hello-world)
3. [路由与请求方法](https://www.google.com/search?q=%233-%E8%B7%AF%E7%94%B1%E4%B8%8E%E8%AF%B7%E6%B1%82%E6%96%B9%E6%B3%95)
4. [解析请求 (Request)](https://www.google.com/search?q=%234-%E8%A7%A3%E6%9E%90%E8%AF%B7%E6%B1%82-request)
5. [构建响应 (Response)](https://www.google.com/search?q=%235-%E6%9E%84%E5%BB%BA%E5%93%8D%E5%BA%94-response)
6. [蓝图 (Blueprint) 模块化](https://www.google.com/search?q=%236-%E8%93%9D%E5%9B%BE-blueprint-%E6%A8%A1%E5%9D%97%E5%8C%96)
7. [中间件拦截器](https://www.google.com/search?q=%237-%E4%B8%AD%E9%97%B4%E4%BB%B6%E6%8B%A6%E6%88%AA%E5%99%A8)
8. [静态文件托管](https://www.google.com/search?q=%238-%E9%9D%99%E6%80%81%E6%96%87%E4%BB%B6%E6%89%98%E7%AE%A1)

---

## 1. 环境准备

在开始编写代码之前，请确保你已经具备以下条件：

* 一块刷入了 **MicroPython** 固件的开发板（推荐 ESP32）。
* 已经将 `lanes.py` 文件上传到了开发板的根目录或 `/lib` 目录中。

> **⚠️ 重要提示：** Lanes 框架本身不负责连接 Wi-Fi。在启动服务器之前，请确保你的开发板已经成功连接到局域网（STA 模式）或开启了热点（AP 模式）。

---

## 2. 第一个 Hello World

创建一个 `main.py`，写下你的第一个 Lanes 应用：

```python
# main.py
import network
import time
from lanes import Lanes

# 1. 简易的 Wi-Fi 连接逻辑 (示例)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('你的WiFi名称', '你的WiFi密码')
while not wlan.isconnected():
    time.sleep(1)
print('网络连接成功:', wlan.ifconfig())

# 2. 初始化 Lanes 框架
app = Lanes(log_level=1) # 启用 INFO 级别日志

# 3. 注册路由
@app.get("/")
def index(req):
    return "Hello, MicroPython World!"

# 4. 启动服务器
if __name__ == "__main__":
    # 默认监听 0.0.0.0:80
    app.run(host="0.0.0.0", port=80)

```

上传并运行 `main.py`，在浏览器中访问开发板的 IP 地址，即可看到 `Hello, MicroPython World!`。

---

## 3. 路由与请求方法

Lanes 支持标准的 HTTP 方法注册，以及动态路由传参。

### 基本方法注册

你可以使用装饰器快速注册对应的方法：

```python
@app.get("/api/data")
def get_data(req):
    return {"message": "这是一个 GET 请求"}

@app.post("/api/data")
def create_data(req):
    return {"message": "这是一个 POST 请求"}
    
# 也支持 @app.put() 和 @app.delete()

```

### 动态路径参数

你可以通过 `:参数名` 的语法在 URL 中提取变量，框架会自动将其作为关键字参数传递给回调函数：

```python
@app.get("/users/:id")
def get_user(req, id):
    return {"user_id": id, "name": f"User_{id}"}

@app.get("/device/:type/:action")
def control_device(req, type, action):
    return {"device_type": type, "action": action}

```

---

## 4. 解析请求 (Request)

每个路由回调函数的第一个参数都是 `Request` 对象，它包含了客户端发来的所有信息。

| 属性 | 描述 | 示例 |
| --- | --- | --- |
| `req.method` | 请求方法 (大写字符串) | `"GET"`, `"POST"` |
| `req.path` | 请求路径 | `"/api/status"` |
| `req.headers` | 请求头 (字典，键为小写) | `{"content-type": "application/json"}` |
| `req.params` | URL 查询参数 (字典) | `?name=esp32` -> `{"name": "esp32"}` |
| `req.body` | 解析后的 JSON 消息体 | `{"switch": "on"}` |
| `req.cookies` | 解析后的 Cookie 字典 | `{"session": "xyz123"}` |

**处理 POST 请求和 Query 参数示例：**

```python
@app.post("/api/config")
def update_config(req):
    # 读取 /api/config?force=true 中的参数
    is_force = req.params.get("force", "false")
    
    # 读取客户端发来的 JSON 载荷
    payload = req.body
    
    return {
        "status": "success",
        "received_data": payload,
        "forced": is_force
    }

```

---

## 5. 构建响应 (Response)

Lanes 提供了极度灵活的响应方式。你可以直接返回数据，框架会智能推断 `Content-Type`，也可以使用 `Response` 对象进行精细控制。

### 快捷返回

* **返回字典/列表**：自动转换为 JSON，状态码默认 `200`。
* **返回字符串**：自动识别是否为 HTML（以 `<html>` 或 `<!doctype` 开头），否则返回普通文本。
* **返回元组**：可以同时指定数据和状态码，例如 `(data, status_code)`。

```python
@app.get("/status")
def status(req):
    # 快捷返回 JSON 和 404 状态码
    return {"error": "Device offline"}, 404

```

### 使用 Response 对象 (高级)

当你需要设置 Cookie 或精确控制响应时，请使用 `Response` 类：

```python
from lanes import Response

@app.post("/login")
def login(req):
    if req.body.get("pwd") == "123456":
        res = Response({"msg": "登录成功"}, 200)
        # 设置 Cookie
        res.set_cookie("token", "admin_token", max_age=3600, httponly=True)
        return res
    else:
        return {"msg": "密码错误"}, 401

```

---

## 6. 蓝图 (Blueprint) 模块化

为了防止 `main.py` 代码过于臃肿，你可以使用 `Blueprint` 将 API 拆分到不同的文件中。

**步骤 1：创建蓝图模块 (例如 `routes/api.py`)**

```python
from lanes import Blueprint

api_bp = Blueprint(url_prefix="/api/v1")

@api_bp.get("/info")
def get_info(req):
    return {"version": "1.0", "device": "ESP32"}

```

**步骤 2：在主程序中注册蓝图**

```python
from lanes import Lanes
from routes.api import api_bp

app = Lanes()
app.register_blueprint(api_bp)

# 现在你可以通过 /api/v1/info 访问该路由了

```

---

## 7. 中间件拦截器

中间件允许你在请求真正到达路由函数之前，执行统一的逻辑，例如权限校验或日志记录。

```python
@app.before_request()
def auth_middleware(req):
    # 假设所有以 /admin 开头的路径都需要校验 Cookie
    if req.path.startswith("/admin"):
        token = req.cookies.get("token")
        if token != "admin_token":
            # 注意：目前的框架设计下，如果在中间件中抛出异常，
            # 会统一返回 500 Internal Error。
            raise Exception("Unauthorized Access")

```

*(注：如果需要在此处直接熔断并返回 401 响应，可根据后续框架的升级特性进行调整。)*

---

## 8. 静态文件托管

在物联网开发中，我们通常需要一个网页仪表盘 (Dashboard)。Lanes 支持直接将开发板内部 Flash 上的文件夹映射到网络路径，并以流式传输（避免内存溢出）。

```python
# 将开发板本地的 "./web" 文件夹，挂载到 URL 的 "/dashboard" 路径下
app.static("/dashboard", "./web")

```

**文件结构示例：**

```text
/ (开发板根目录)
├── lanes.py
├── main.py
└── web/
    ├── index.html
    ├── style.css
    └── app.js

```

访问 `http://<开发板IP>/dashboard/index.html` 即可加载该网页。框架会自动处理 `text/html`、`text/css`、`application/javascript` 等常见 MIME 类型。