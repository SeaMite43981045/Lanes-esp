import time
import asyncio
import json

try:
    from micropython import const # type: ignore
except ImportError:
    def const(x):
        return x

LOG_DEBUG = const(0)
LOG_INFO  = const(1)
LOG_WARN  = const(2)
LOG_ERROR = const(3)
LOG_FATAL = const(4)

HTTP_OK                    = const(200)
HTTP_NO_CONTENT            = const(204)
HTTP_NOT_MODIFIED          = const(304)
HTTP_BAD_REQUEST           = const(400)
HTTP_UNAUTHORIZED          = const(401)
HTTP_NOT_FOUND             = const(404)
HTTP_METHOD_NOT_ALLOWED    = const(405)
HTTP_SERVER_ERROR          = const(500)

HTTP_PHRASES = {
    200: "OK",
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
METHODS = const((METHOD_GET, METHOD_POST, METHOD_PUT, METHOD_DELETE))

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

class LanesMethodError(Exception):
    def __init__(self, message, *args: object) -> None:
        super().__init__(*args)
        self.message = message
    def __str__(self) -> str:
        return self.message

class Lanes:
    def __init__(self, log_level=LOG_INFO):
        self.routes = {
            "GET": {},
            "POST": {},
            "PUT": {},
            "DELETE": {}
        }
        self.logger = Logger(log_level)
        
    def make_header(self, writer: asyncio.StreamWriter, status=HTTP_OK, body = "", headers = {}):
        writer.write(f"HTTP/1.1 {status} {HTTP_PHRASES[status]}\r\n".encode())
        writer.write(f"Content-Length: {len(body)}\r\n".encode())
        writer.write(f"Allow: {METHOD_GET}, {METHOD_POST}, {METHOD_PUT}, {METHOD_DELETE}\r\n".encode())
        writer.write(b"Server: Lanes/1.0 (esp32)\r\n")
        for (key, value) in headers.items():
            writer.write(f"{key}: {value}\r\n".encode())
        writer.write(b"\r\n")

    async def send_json(self, writer: asyncio.StreamWriter, status=HTTP_OK, data = None):
        body = json.dumps(data)
        self.make_header(writer, status, body, {"Content-Type": "application/json"})
        writer.write(body.encode())
        
        await writer.drain()

    async def send_text(self, writer: asyncio.StreamWriter, status=HTTP_OK, body: str = ""):
        self.make_header(writer, status, body, {"Content-Type": "text/plain"})
        writer.write(body.encode())
        
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
                param_val = path_chunk[i]

                params[param_key] = param_val
            else:
                if route_chunk[i] != path_chunk[i]:
                    return (False, params)
        
        return (True, params)

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

                    headers[header_chunk[0]] = header_chunk[1]
            
            request_chunk = request_line.split(" ")

            if len(request_chunk) != 3:
                await self.send_json(writer, HTTP_BAD_REQUEST, {"message": "Bad request"})
                return
            
            method = request_chunk[0].upper()
            path = request_chunk[1]
            protocol = request_chunk[2]

            if method not in METHODS:
                await self.send_json(writer, HTTP_METHOD_NOT_ALLOWED, {"message": "Method not allowed"})
                return

            self.logger.debug(f"method: {method} path: {path} protocol: {protocol}")
            
            params = {}
            matched = False
            matched_route = ""

            for route in self.routes[method].keys():
                match_result = self.match_path(route, path)
                if match_result[0]:
                    params = match_result[1]
                    matched = True
                    matched_route = route
                    break
            
            if matched:
                callback = self.routes[method][matched_route]
                res = callback(**params)
            else:
                await self.send_json(writer, HTTP_NOT_FOUND, {"message": "Page no found"})
                return

            if isinstance(res, (dict, list)):
                await self.send_json(writer, HTTP_OK, res)
            else:
                await self.send_text(writer, HTTP_OK, str(res))

        except Exception as e:
            self.logger.error(f"Handle request error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    # Route registery functions
    def register_route(self, method, path, callback):
        if method not in METHODS:
            raise LanesMethodError(f"The method '{method}' is not allowed!")
        self.routes[method][path] = callback
    
    def route(self, path, method=METHOD_GET):
        if method not in METHODS:
            raise LanesMethodError(f"The method '{method}' is not allowed!")
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
    
    async def run_server(self, host="0.0.0.0", port=80):
        server = await asyncio.start_server(self.handle_request, host, port)
        self.logger.info("The server is running on: {}:{}".format(host, port))
        async with server:
            try:
                await server.serve_forever()
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass
            finally:
                server.close()
                await server.wait_closed()
                self.logger.info("================")
                self.logger.info("Server is closed")
                self.logger.info("================")
    
    def run(self, host="0.0.0.0", port=80):
        asyncio.run(self.run_server(host, port))
