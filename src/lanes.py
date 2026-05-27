import time
import asyncio
import json
import os

try:
    from micropython import const # type: ignore
except ImportError:
    def const(x):
        return x

__version__ = "1.2.0-pre"

LOG_DEBUG = const(0)
LOG_INFO  = const(1)
LOG_WARN  = const(2)
LOG_ERROR = const(3)
LOG_FATAL = const(4)

HTTP_OK                    = const(200)
HTTP_CREATED               = const(201)
HTTP_ACCEPTED              = const(202)
HTTP_NO_CONTENT            = const(204)
HTTP_NOT_MODIFIED          = const(304)
HTTP_BAD_REQUEST           = const(400)
HTTP_UNAUTHORIZED          = const(401)
HTTP_NOT_FOUND             = const(404)
HTTP_METHOD_NOT_ALLOWED    = const(405)
HTTP_SERVER_ERROR          = const(500)

HTTP_ERROR_STATUSES = [400, 401, 402, 403, 404, 405, 500, 501, 502, 503, 504, 505]

HTTP_PHRASES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error"
}

METHOD_GET = const("GET")
METHOD_POST = const("POST")
METHOD_PUT = const("PUT")
METHOD_DELETE = const("DELETE")
METHOD_OPTIONS = const("OPTIONS")
METHODS = const((METHOD_GET, METHOD_POST, METHOD_PUT, METHOD_DELETE, METHOD_OPTIONS))

MIME_TYPES = {
    "plain": "text/plain; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "css": "text/css",
    "js": "application/javascript",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "ico": "image/x-icon",
    "json": "application/json"
}

def get_time_str():
    t = time.localtime()
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

class Logger:
    def __init__(self, log_level = LOG_INFO):
        self.log_level = log_level
    
    def output(self, log_level, prefix, message):
        if (log_level >= self.log_level):
            print(f"[{get_time_str()}] {prefix} -", message)

    def debug(self, message):
        self.output(LOG_DEBUG, "[DEBUG]", message)

    def info(self, message):
        self.output(LOG_INFO, "[INFO] ", message)

    def warn(self, message):
        self.output(LOG_WARN, "[WARN] ", message)

    def error(self, message):
        self.output(LOG_ERROR, "[ERROR]", message)

    def fatal(self, message):
        self.output(LOG_FATAL, "[FATAL]", message)

class Request:
    def __init__(self, method, path, headers: dict, params, body):
        self.method = method
        self.path = path
        self.headers = headers
        self.params = params
        self.body = body
        self.ctx = {}
        self.cookies = {}

        self._parse_cookies()
    
    def _parse_cookies(self):
        raw_cookie: str = self.headers.get("cookie", "")

        if not raw_cookie or raw_cookie == "":
            return
        
        parts = raw_cookie.split(";")
        for part in parts:
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                self.cookies[k] = v

class Response:
    def __init__(self, body = None, headers = None, status: int = HTTP_OK, content_type = MIME_TYPES["plain"]) -> None:
        headers = headers if not headers == None else {}

        self.body = body
        self.headers = headers
        self.status = status
        self.content_type = content_type
        self._cookies = []

    def set_cookie(self, key, value, max_age=None, path="/", httponly=False, secure=False):
        cookie_parts = [f"{key}={value}"]
        
        if path:
            cookie_parts.append(f"Path={path}")
        if max_age is not None:
            cookie_parts.append(f"Max-Age={max_age}")
        if httponly:
            cookie_parts.append("HttpOnly")
        if secure:
            cookie_parts.append("Secure")
            
        cookie_str = "; ".join(cookie_parts)
        self._cookies.append(cookie_str)

class Blueprint:
    def __init__(self, url_prefix: str = "/") -> None:
        self.url_prefix = url_prefix
        self.routes = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "DELETE": {}
        }
        self.middlewares = []
    
    # Route registery functions
    def register_route(self, method, path, callback):
        if method not in METHODS:
            raise ValueError(f"The method '{method}' is not allowed!")
        self.routes[method][path] = callback
    
    def route(self, path, method=METHOD_GET):
        if method not in METHODS:
            raise ValueError(f"The method '{method}' is not allowed!")
        def wrapper(func):
            self.routes[method][path] = func
            return func
        return wrapper
    
    def get(self, path):
        def wrapper(func):
            self.routes["GET"][path] = func
            return func
        return wrapper

    def post(self, path):
        def wrapper(func):
            self.routes["POST"][path] = func
            return func
        return wrapper
    
    def put(self, path):
        def wrapper(func):
            self.routes["PUT"][path] = func
            return func
        return wrapper
    
    def delete(self, path):
        def wrapper(func):
            self.routes["DELETE"][path] = func
            return func
        return wrapper
    
    # Middleware registery functions
    def before_request(self):
        def wrapper(func):
            self.middlewares.append(func)
            return func
        return wrapper

class Lanes:
    config = {
        "server": {
            "host": str,
            "port": int
        },
        "static": {
            "path": str
        }
    }

    _dummy_generator_obj = (lambda: (yield))()
    _GENERATOR_OBJECT_TYPE = type(_dummy_generator_obj)

    def __init__(self, log_level=LOG_INFO):
        self.routes = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "DELETE": {}
        }
        self.static_routes = {}
        self.middlewares = []
        self.error_handlers: dict[int, list] = {status: [] for status in HTTP_ERROR_STATUSES}
        self.logger = Logger(log_level)
        self.config["static"]["path"] = "./assets"
    
    def static(self, url_prefix: str, folder_path: str):
        if not url_prefix.startswith("/"):
            url_prefix = "/" + url_prefix
        if url_prefix.endswith("/") and url_prefix != "/":
            url_prefix = url_prefix.rstrip("/")

        self.static_routes[url_prefix] = folder_path
        self.logger.info(f"Register static directory: {url_prefix} -> {folder_path}")
        
    def make_header(self, writer: asyncio.StreamWriter, status=HTTP_OK, headers = None):
        headers = headers if headers is not None else {}
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "Content-Type"

        writer.write(f"HTTP/1.1 {status} {HTTP_PHRASES.get(status, "Unknown")}\r\n".encode())
        writer.write(f"Allow: {METHOD_GET}, {METHOD_POST}, {METHOD_PUT}, {METHOD_DELETE}, {METHOD_OPTIONS}\r\n".encode())
        writer.write(b"Server: Lanes/1.0 (esp32)\r\n")

        for key, value in headers.items():
            if isinstance(value, (list, tuple)):
                for val in value:
                    writer.write(f"{key}: {val}\r\n".encode("utf-8"))
            else:
                writer.write(f"{key}: {value}\r\n".encode("utf-8"))
                
        writer.write(b"\r\n")

    async def make_response(self, writer: asyncio.StreamWriter, data, mime_type=MIME_TYPES["plain"], status = HTTP_OK, headers = None):
        body = None
        headers = headers if headers is not None else {}
        
        if mime_type == MIME_TYPES["json"]:
            body = json.dumps(data)
        else:
            body=data

        headers["Content-Length"] = len(body)
        headers["Content-Type"] = mime_type
        
        self.make_header(writer, status, headers)
        writer.write(body.encode())

        await writer.drain()
    
    async def send_file(self, writer: asyncio.StreamWriter, req: Request, method, file_path, path):
        self.logger.debug(f"target file path: {file_path}")

        if not os.path.exists(file_path):
            self.logger.info(f"{method} {file_path} - {HTTP_NOT_FOUND} {HTTP_PHRASES[HTTP_NOT_FOUND]}")
            await self.handle_error(writer, HTTP_NOT_FOUND, req, f"Could not {method} {path}")
            return

        file_ext = file_path.split(".")[-1]
        content_type = MIME_TYPES.get(file_ext, "application/octet-stream")
        self.make_header(writer, HTTP_OK, { "Content-Type": content_type })

        buffer = bytearray(1024)
        with open(file_path, "rb") as f:
            while True:
                n = f.readinto(buffer)
                if n == 0:
                    break
                writer.write(buffer[:n])
                await writer.drain()
    
    def match_path(self, route: str, path: str):
        route_chunk = route.split("/")
        path_chunk = path.split("/")

        params = {}

        if len(route_chunk) != len(path_chunk):
            return (False, params)
        
        for i in range(len(route_chunk)):
            if (route_chunk[i].startswith(":")):
                param_key = route_chunk[i].replace(":", "", 1)
                param_val = path_chunk[i].split("?", 1)[0]

                params[param_key] = param_val
            else:
                if route_chunk[i] != path_chunk[i]:
                    return (False, params)
        
        return (True, params)
    
    async def dispatch_request(self, handler, req, **kwargs):
        res = handler(req, **kwargs)
        
        if isinstance(res, self._GENERATOR_OBJECT_TYPE):
            actual_response = await res
            return actual_response
        else:
            return res
        
    async def handle_error(self, writer: asyncio.StreamWriter, status: int, req: Request, error_message: str | None = None):
        if error_message is None:
            error_message = HTTP_PHRASES.get(status, "Unknown Error")
        
        handlers = self.error_handlers.get(status, [])

        if handlers:
            try:
                for error_handler in handlers:
                    callback_result = await self.dispatch_request(error_handler, req)
                    
                    if callback_result is not None:
                        response = await self.get_response(callback_result)
                        await self.handle_response(writer, response)
                        return
                    
                await self.make_response(writer, {"message": error_message}, MIME_TYPES["json"], status)
                return
            except Exception as e:
                self.logger.error(f"An error occurred in custom error handler: {e}")
                if status != HTTP_SERVER_ERROR:
                    await self.handle_error(writer, HTTP_SERVER_ERROR, req)
                    return
                else:
                    await self.make_response(writer, {"message": "Internal error"}, MIME_TYPES["json"], HTTP_SERVER_ERROR)
                    return
        else:
            await self.make_response(writer, {"message": error_message}, MIME_TYPES["json"], status)
            return
        
    async def handle_response(self, writer: asyncio.StreamWriter, response: Response):
        status = response.status
        headers = response.headers
        body = response.body
        content_type = response.content_type

        if response._cookies:
            headers["Set-Cookie"] = response._cookies

        headers["Content-Type"] = content_type

        await self.make_response(writer, body, content_type, status, headers)
    
    async def get_response(self, callback_result):
        response = Response()

        if isinstance(callback_result, tuple) and len(callback_result) == 2 and isinstance(callback_result[1], int):
            response.status = callback_result[1]
            callback_result = callback_result[0]

        if isinstance(callback_result, Response):
            response = callback_result
        elif isinstance(callback_result, (dict, list)):
            response.body = callback_result
            response.content_type = MIME_TYPES["json"]
        else:
            response.body = str(callback_result)
            response.content_type = MIME_TYPES["plain"]
        
        return response

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            raw_line = await reader.readline()
            if not raw_line:
                return
            
            request_line = raw_line.decode().strip()
            headers = {}
            self.logger.debug(f"request line: {request_line}")

            while True:
                header_raw_line = await reader.readline()
                if header_raw_line == b'\r\n' or header_raw_line == b'\n' or not header_raw_line:
                    break
                header_line = header_raw_line.decode().strip()
                if ":" in header_line:
                    header_chunk = header_line.split(":", 1)

                    headers[header_chunk[0].strip().lower()] = header_chunk[1].strip()
            
            request_chunk = request_line.split(" ")

            if len(request_chunk) != 3:
                await self.make_response(writer, {"message": "Bad request"}, MIME_TYPES["json"], HTTP_BAD_REQUEST)
                return
            
            method = request_chunk[0].upper()
            raw_path = request_chunk[1]
            protocol = request_chunk[2]
            
            path = ""
            query_string = ""
            raw_path_chunk = raw_path.split("?", 1)

            if len(raw_path_chunk) == 1:
                path = raw_path
            else:
                path = raw_path_chunk[0]
                query_string = raw_path_chunk[1]

            if path.endswith("/") and path != "/":
                path = path.removesuffix("/")
            
            self.logger.debug(f"method: {method} path: {path} protocol: {protocol}")
            
            route_params = {}
            matched = False
            matched_route = ""

            for route in self.routes[method]:
                match_result = self.match_path(route, path)
                if match_result[0]:
                    route_params = match_result[1]
                    matched = True
                    matched_route = route
                    break

            # Body handler
            content_length = int(headers.get("content-length", 0))
            raw_body = b"{}"
            if content_length > 0:
                raw_body = (await reader.read(content_length)).strip()
            self.logger.debug(raw_body)

            try:
                body = json.loads(raw_body.decode())
            except ValueError:
                self.logger.info(f"{method} {path} - {HTTP_BAD_REQUEST} {HTTP_PHRASES[HTTP_BAD_REQUEST]}")
                await self.make_response(writer, {"message": "Wrong body struct"}, MIME_TYPES["json"], HTTP_BAD_REQUEST)
                return

            self.logger.debug(body)

            # Params parse
            params = {}

            if query_string != "":
                params_chunk = query_string.split("&")
                for raw_param in params_chunk:
                    if "=" in raw_param:
                        param_chunk = raw_param.split("=", 1)
                        params[param_chunk[0]] = param_chunk[1]
            
            req = Request(method, path, headers, params, body)

            if method not in METHODS:
                self.logger.info(f"{method} {path} - {HTTP_METHOD_NOT_ALLOWED} {HTTP_PHRASES[HTTP_METHOD_NOT_ALLOWED]}")
                await self.handle_error(writer, HTTP_METHOD_NOT_ALLOWED, req)
                return
            if method == METHOD_OPTIONS:
                self.logger.info(f"{method} {path} - {HTTP_NO_CONTENT} {HTTP_PHRASES[HTTP_NO_CONTENT]}")
                self.make_header(writer, HTTP_NO_CONTENT)
                await writer.drain()
                return
            
            # Middlewares
            for middleware in self.middlewares:
                try:
                    result = await self.dispatch_request(middleware, req)
                    if result is not None:
                        response = await self.get_response(result)
                        await self.handle_response(writer, response)
                        self.logger.info(f"{method} {path} - {response.status} {HTTP_PHRASES[response.status]}")
                        return
                except Exception as e:
                    self.logger.info(f"{method} {path} - {HTTP_SERVER_ERROR} {HTTP_PHRASES[HTTP_SERVER_ERROR]}")
                    await self.handle_error(writer, HTTP_SERVER_ERROR, req)
                    return
            
            # Function callback
            if matched:
                callback = self.routes[method][matched_route]
                try:
                    callback_result = await self.dispatch_request(callback, req, **route_params)
                except Exception as e:
                    self.logger.info(f"{method} {path} - {HTTP_SERVER_ERROR} {HTTP_PHRASES[HTTP_SERVER_ERROR]}")
                    await self.handle_error(writer, HTTP_SERVER_ERROR, req)
                    return
            else:
                target_file_path = None

                for prefix, folder in self.static_routes.items():
                    if path.startswith(prefix):
                        rel_path = path[len(prefix):].lstrip("/")
                        target_file_path = os.path.join(folder, rel_path)
                        break
                
                if not target_file_path:
                    rel_path = path.lstrip("/")
                    target_file_path = os.path.join(self.config["static"]["path"], rel_path)
                
                await self.send_file(writer, req, method, target_file_path, path)
                return
            
            response = await self.get_response(callback_result)

            await self.handle_response(writer, response)

            self.logger.info(f"{method} {path} - {response.status} {HTTP_PHRASES[response.status]}")
        except Exception as e:
            self.logger.error(f"Handle request error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    # Route registery functions
    def register_route(self, method, path, callback):
        if method not in METHODS:
            raise ValueError(f"The method '{method}' is not allowed!")
        self.routes[method][path] = callback
    
    def route(self, path, method=METHOD_GET):
        if method not in METHODS:
            raise ValueError(f"The method '{method}' is not allowed!")
        def wrapper(func):
            self.routes[method][path] = func
            return func
        return wrapper
    
    def get(self, path):
        def wrapper(func):
            self.routes["GET"][path] = func
            return func
        return wrapper

    def post(self, path):
        def wrapper(func):
            self.routes["POST"][path] = func
            return func
        return wrapper
    
    def put(self, path):
        def wrapper(func):
            self.routes["PUT"][path] = func
            return func
        return wrapper
    
    def delete(self, path):
        def wrapper(func):
            self.routes["DELETE"][path] = func
            return func
        return wrapper
    
    # Middleware registery functions
    def before_request(self):
        def wrapper(func):
            self.middlewares.append(func)
            return func
        return wrapper
    
    # Blueprint registery functions
    def register_blueprint(self, blueprint: Blueprint):
        url_prefix = blueprint.url_prefix
        # Register routes
        for method in blueprint.routes:
            for path in blueprint.routes[method]:
                self.routes[method][url_prefix if path == "/" else url_prefix + path] = blueprint.routes[method][path]
        
        # Register middlewares
        for middleware in blueprint.middlewares:
            self.middlewares.append(middleware)

        self.logger.info("Register blueprint: " + url_prefix)

    # Error handler registery functions
    def error_handler(self, status: int):
        if status not in HTTP_PHRASES:
            raise ValueError(f"Status {status} is not supported!")
        if not str(status).startswith(("4", "5")):
            raise ValueError(f"Status {status} is not an error status!")
        
        def wrapper(func):
            self.error_handlers[status].append(func)
            return func
        return wrapper
    
    async def run_server(self):
        host = self.config["server"]["host"]
        port = self.config["server"]["port"]
        server = await asyncio.start_server(self.handle_request, host, port)

        self.logger.info("=======================================")
        self.logger.info("The server is running on: {}:{}".format(host, port))
        self.logger.info("=======================================")

        self.logger.debug(f"routes: {self.routes}")
        
        try:
            while True:
                await asyncio.sleep(3600)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            server.close()
            await server.wait_closed()

            self.logger.info("=================")
            self.logger.info("Server is closed")
            self.logger.info("=================")
    
    def run(self, host="0.0.0.0", port=80):
        self.config["server"]["host"] = host
        self.config["server"]["port"] = port
        asyncio.run(self.run_server())


def render_template(path: str, **params):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template '{path}' not found!")
    
    with open(path, "r", encoding="utf-8") as f:
        template = f.read()
    
    for key, value in params.items():
        placeholder = "{{ " + key + " }}"
        template = template.replace(placeholder, str(value))

    res = Response(template, content_type=MIME_TYPES["html"])
    
    return res