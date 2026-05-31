# Lanes

Lanes 是一个专为 **MicroPython** 打造的轻量级、高性能、异步 Web 框架（针对 ESP32 及类似资源受限的微控制器进行了深度优化）。Lanes 吸取了 Flask 和 Sanic 等现代桌面级框架的设计灵感，为嵌入式开发带来了表现力强、基于装饰器的路由系统和标准的 HTTP 抽象。

**当前版本:** `1.3.0`

---

## 🚀 功能特性

* **异步核心：** 完全基于 MicroPython 的 `asyncio` 构建，确保非阻塞的 I/O 操作。
* **表现力丰富的路由：** 支持显式装饰器（如 `@app.get`、`@app.post` 等）和动态 URL 路径参数（例如 `/api/sensor/:id`）。
* **模块化架构：** 使用 `Blueprint`（蓝图）模块，轻松将你的应用拆分成多个独立的业务模块。
* **静态文件托管：** 内置流式传输机制，可直接从设备的物理文件系统（`os.path`）托管和渲染资源文件（CSS、JS、图片）。
* **模板引擎：** 内置轻量级模板渲染器（`render_template`），支持通过 `{{ keyword }}` 语法进行动态占位符替换。
* **中间件钩子：** 利用前置拦截器（`@app.before_request`），在全局或蓝图模块内对传入的请求进行统一预处理。
* **自定义错误处理：** 支持使用 `@app.error_handler(status)` 装饰器将特定的 HTTP 错误状态码（`4xx`、`5xx`）直接映射到自定义的回调函数中。

---

## 🛠️ 快速开始

下面是一个简单的示例，展示了在微控制器上使用 Lanes 搭建 Web 服务器有多么简单：

```python
import asyncio
from lanes import Lanes, render_template

app = Lanes()

# 1. 基础纯文本路由
@app.get("/")
def index(req):
    return "Hello from Lanes!"

# 2. 动态路径参数路由
@app.get("/api/hardware/:pin")
def read_pin(req, pin):
    return {"pin_requested": pin, "status": "high"}

# 3. 处理带 JSON 负载的 POST 请求
@app.post("/api/led/control")
def control_led(req):
    state = req.body.get("state", "off")
    # 在这里添加你的硬件交互逻辑（例如使用 machine.Pin）
    return {"success": True, "new_state": state}

# 4. 渲染 HTML 模板
@app.get("/dashboard")
def view_dashboard(req):
    return render_template("templates/index.html", title="ESP32 Board", status="Active")

# 5. 启动服务器
if __name__ == "__main__":
    # 主机地址默认为 0.0.0.0，端口默认为 80
    app.run(host="0.0.0.0", port=80)
```

---

## 📁 推荐目录结构

为了充分利用框架内置的静态资源托管和模板渲染工具，建议将您的 MicroPython 项目组织如下：

```text
├── main.py              # 服务器入口文件
├── lanes.py             # Lanes 核心框架文件
├── assets/              # 默认静态资源文件夹（存放 CSS、JS、图标等）
│   ├── style.css
│   └── script.js
└── templates/           # HTML 模板文件夹
    └── index.html
```

---

## 📖 详细文档 (Wiki)

如果您想深入了解框架的架构教程、完整的 API 参考手册以及包含中间件、蓝图、请求/响应生命周期的代码示例，请访问我们的官方 Wiki 页面：

* 🌐 **GitHub 文档：** [GitHub Wiki](https://github.com/SeaMite43981045/Lanes-esp/wiki)
* 🇨🇳 **Gitee 文档（国内镜像）：** [Gitee Wiki](https://gitee.com/SeaMite43981045/Lanes-esp/wikis)

---

## 📄 开源协议

本项目基于 **MIT License** 协议开源，协议全文如下：

```text
MIT License

Copyright (c) 2026 SeaMite43981045

特此授权，免费向任何获得本软件副本及相关文档文件（下称“软件”）的人士授予不受限制的处理本软件的权利，包括但不限于使用、复制、修改、合并、发布、分发、再许可和/或出售本软件副本的权利，并允许向其提供本软件的人士在满足以下条件的前提下这样做：

上述版权声明和本许可声明应包含在本软件的所有副本或实质性部分中。

本软件按“原样”提供，不作任何形式的明示或暗示保证，包括但不限于对适销性、特定用途的适用性和非侵权性的保证。在任何情况下，无论是因合同诉讼、侵权诉讼或其他原因引起的、由本软件或本软件的使用或其他交易引起的或与之相关的任何索赔、损害或其他责任，作者或版权所有者均不承担任何责任。