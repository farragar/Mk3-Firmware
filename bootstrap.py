# TiLDA Badge Bootstrap script
# Automatically downloads the app library to the badge via wifi
import network, pyb, usocket, machine, os, json, ugfx, ujson, hashlib, binascii

### START lib/http_client.py ###
try:
	import ussl
	SUPPORT_SSL = True
except ImportError:
	ussl = None
	SUPPORT_SSL = False

SUPPORT_TIMEOUT = hasattr(usocket.socket, 'settimeout')
CONTENT_TYPE_JSON = 'application/json'
DELAY_BETWEEN_READS = 50
BUFFER_SIZE = 128

class Response(object):
	def __init__(self):
		self.encoding = 'utf-8'
		self.headers = {}
		self.status = None
		self.socket = None
		self._content = None

	# Hands the responsibility for a socket over to this reponse. This needs to happen
	# before any content can be inspected
	def add_socket(self, socket, content_so_far):
		self.content_so_far = content_so_far
		self.socket = socket

	@property
	def content(self):
		if not self._content:
			if not self.socket:
				raise OSError("Invalid response socket state. Has the content been downloaded instead?")
			try:
				if "Content-Length" not in self.headers:
					raise Exception("No Content-Length")
				content_length = int(self.headers["Content-Length"])
				self._content = self.content_so_far
				del self.content_so_far
				while len(self._content) < content_length:
					pyb.delay(DELAY_BETWEEN_READS)
					buf = self.socket.recv(BUFFER_SIZE)
					self._content += buf

			finally:
				self.close()
		return self._content;

	@property
	def text(self):
		return str(self.content, self.encoding) if self.content else ''

	# If you don't use the content of a Response at all you need to manually close it
	def close(self):
		if self.socket is not None:
			self.socket.close()
			self.socket = None

	def json(self):
		return ujson.loads(self.text)

	# Writes content into a file. This function will write while receiving, which avoids
	# having to load all content into memory
	def download_to(self, target):
		if not self.socket:
			raise OSError("Invalid response socket state. Has the content already been consumed?")
		try:
			if "Content-Length" not in self.headers:
				raise Exception("No Content-Length")
			remaining = int(self.headers["Content-Length"])

			with open(target, 'wb') as f:
				f.write(self.content_so_far)
				remaining -= len(self.content_so_far)
				del self.content_so_far
				while remaining > 0:
					pyb.delay(DELAY_BETWEEN_READS)
					buf = self.socket.recv(BUFFER_SIZE)
					f.write(buf)
					remaining -= len(buf)
				f.flush()
			os.sync()

		finally:
			self.close()

	def raise_for_status(self):
		if 400 <= self.status < 500:
			raise OSError('Client error: %s' % self.status)
		if 500 <= self.status < 600:
			raise OSError('Server error: %s' % self.status)
		return self

	# In case you want to use "with"
	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

def open_http_socket(method, url, json=None, timeout=None, headers=None, urlencoded = None):
	urlparts = url.split('/', 3)
	proto = urlparts[0]
	host = urlparts[2]
	urlpath = '' if len(urlparts) < 4 else urlparts[3]

	if proto == 'http:':
		port = 80
	elif proto == 'https:':
		port = 443
	else:
		raise OSError('Unsupported protocol: %s' % proto[:-1])

	if ':' in host:
		host, port = host.split(':')
		port = int(port)

	if json is not None:
		content = ujson.dumps(json)
		content_type = CONTENT_TYPE_JSON
	elif urlencoded is not None:
		content = urlencoded
		content_type = "application/x-www-form-urlencoded"
	else:
		content = None

	# ToDo: Detect IP addresses and skip the lookup
	ai = usocket.getaddrinfo(host, port)
	addr = ai[0][4]

	sock = usocket.socket()

	if timeout is not None:
		assert SUPPORT_TIMEOUT, 'Socket does not support timeout'
		sock.settimeout(timeout)

	sock.connect(addr)

	if proto == 'https:':
		assert SUPPORT_SSL, 'HTTPS not supported: could not find ussl'
		sock = ussl.wrap_socket(sock)

	sock.send('%s /%s HTTP/1.0\r\nHost: %s\r\n' % (method, urlpath, host))

	if headers is not None:
		for header in headers.items():
			sock.send('%s: %s\r\n' % header)

	if content is not None:
		sock.send('content-length: %s\r\n' % len(content))
		sock.send('content-type: %s\r\n' % content_type)
		sock.send('\r\n')
		sock.send(content)
	else:
		sock.send('\r\n')

	return sock

# Adapted from upip
def request(method, url, json=None, timeout=None, headers=None, urlencoded=None):
	sock = open_http_socket(method, url, json, timeout, headers, urlencoded)
	try:
		response = Response()
		state = 1
		hbuf = b"";
		remaining = None;
		while True:
			pyb.delay(DELAY_BETWEEN_READS)
			buf = sock.recv(BUFFER_SIZE)
			if state == 1: # Status
				nl = buf.find(b"\n")
				if nl > -1:
					hbuf += buf[:nl - 1]
					response.status = int(hbuf.split(b' ')[1])
					state = 2
					hbuf = b"";
					buf = buf[nl + 1:]
				else:
					hbuf += buf

			if state == 2: # Headers
				hbuf += buf
				nl = hbuf.find(b"\n")
				while nl > -1:
					if nl < 2:
						buf = hbuf[2:]
						hbuf = None
						state = 3
						break

					header = hbuf[:nl - 1].decode("utf8").split(':', 3)
					response.headers[header[0].strip()] = header[1].strip()
					hbuf = hbuf[nl + 1:]
					nl = hbuf.find(b"\n")

			if state == 3: # Content
				response.add_socket(sock, buf)
				sock = None # It's not our responsibility to close the socket anymore
				return response
	finally:
		if sock: sock.close()

def get(url, **kwargs):
	return request('GET', url, **kwargs)

### END lib/http_client.py ###

def calculate_hash(filename):
	try:
		with open(filename, "rb") as file:
			sha256 = hashlib.sha256()
			buf = file.read(128)
			while len(buf) > 0:
				sha256.update(buf)
				buf = file.read(128)
			return str(binascii.hexlify(sha256.digest()), "utf8")
	except:
		return "ERR"

def download(url, target, expected_hash):
	while True:
		get(url).raise_for_status().download_to(target)
		if calculate_hash(target) == expected_hash:
			break

ugfx.init()
ugfx.clear(ugfx.WHITE)
ugfx.text(5, 5, "Downloading TiLDA software", ugfx.BLACK)
label = ugfx.Label(5, 30, ugfx.width() - 10, ugfx.height() - 30, "Please wait")

w = {}
try:
	if "wifi.json" in os.listdir():
		with open("wifi.json") as f:
			w = json.loads(f.read())
except ValueError as e:
	print(e)

wifi_info = "\nMore information:\nbadge.emfcamp.org/TiLDA_MK3/wifi"
if not ("ssid" in w and "pw" in w):
	label.text("Couldn't find a valid wifi.json :(" + wifi_info)
	while True: pyb.wfi()

label.text("Connecting to '%s'.\nIf this is incorrect, please check your wifi.json%s" % (w["ssid"], wifi_info))
n = network.CC3100()
if ("pw" in w) and w["pw"]:
	n.connect(w["ssid"], w["pw"], timeout=10)
else:
	n.connect(w["ssid"], timeout=10)

for d in ["apps", "apps/app_library", "lib"]:
	try:
		os.mkdir(d)
	except OSError as e:
		print(e)

try:
	URL = "http://api.badge.emfcamp.org/firmware"
	label.text("Downloading list of libraries")
	master = get(URL + "/master.json").raise_for_status().json()
	libs_to_update = []
	for i, (lib, expected_hash) in enumerate(master["lib"].items()):
		label.text("Downloading library: %s (%d/%d)" % (lib, i + 1, len(master["lib"])))
		download(URL + "/master/lib/%s" % lib, "lib/%s" % lib, expected_hash)

	label.text("Downloading app library")
	download(URL + "/master/apps/app_library/main.py", "apps/app_library/main.py", master["apps"]["app_library"]["main.py"])

finally:
	os.sync()
	label.destroy()
machine.reset()
