import json
from json.decoder import JSONDecodeError

from django.core.handlers.wsgi import WSGIRequest


class HttpRequest(WSGIRequest):
	"""A HTTP request extends WSGIRequest."""

	def __init__(self, environ):
		super(HttpRequest, self).__init__(environ)
		self._str = ''
		self._data = self._merge_data()
		self.extra_data = {}

	def _merge_data(self):
		"""
		Merge the GET and POST data together
		"""
		get_data = self.GET
		post_data = self.POST
		# 1）`body`为`form-data`、`application/x-www-form-urlencoded`格式数据
		if post_data:
			return {**get_data, **post_data}
		# 2）`body`为`json`、`text`等其他形式数据
		post_body = self.body
		if not post_body:
			return {**get_data}
		json_body = dict()
		try:
			json_body = json.loads(post_body)
		except JSONDecodeError:
			self._str = post_body
		finally:
			return {**get_data, **json_body}

	def __contains__(self, item):
		"""
		``x in HttpRequest`` is an alias for ``x in HttpRequest.data``
		"""
		return item in self.data

	@property
	def data(self):
		"""
		The QueryString data and Body data of a request are
		returned as a 'Python' data structure, usually a 'dict'.
		"""
		return self._data

	@property
	def str(self):
		return self._str

	def get(self, *args, **kwargs):
		"""
		`HttpRequest.get(...)` is an alias for `BaseResponse.data.get(...)`
		"""
		return self.data.get(*args, **kwargs)


def convert_request(request):
	if not request.__dict__.get('arkfbp_request', None):
		_request = HttpRequest(request.environ)
		request.__dict__.update(arkfbp_request=_request)
		_request.__dict__.update(request=request)

	return request.__dict__.get('arkfbp_request')
