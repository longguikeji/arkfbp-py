class HttpRequest:
	"""A basic HTTP request."""

	def __init__(self):
		self.QUERY_PARAMS = {}
		self.BODY = {}
		self.COOKIES = {}
		self.META = {}
		self.FILES = {}
		self.path = ''
		self.path_info = ''
		self.method = None
		self.content_type = None
		self.content_params = None
		self.schema = None
		self.encoding = None

	@property
	def headers(self):
		# TODO 头部信息缓存 + 解析头部信息友好展示
		return self.META
