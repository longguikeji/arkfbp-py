import copy
import json
from json.decoder import JSONDecodeError

from django.core.handlers.wsgi import WSGIRequest


class HttpRequest(WSGIRequest):
	"""A HTTP request extends WSGIRequest."""
	def __init__(self, request):
		self._request = request
		self._str = ''
		self._data = self._merge_data()
		self.extra_data = {}
		super(HttpRequest, self).__init__(request.environ)

	def _merge_data(self):
		"""
		Merge the GET and POST data together
		"""
		_get_params = {key: value for key, value in self._request.GET.items()}
		_post_params = {key: value for key, value in self._request.POST.items()}

		# 1）`body`为`form-data`、`application/x-www-form-urlencoded`格式数据
		if _post_params:
			return {**_get_params, **_post_params}
		# 2）`body`为`json`、`text`等其他形式数据
		_post_body = self._request.body
		if not _post_body:
			return {**_get_params}
		json_body = dict()
		try:
			json_body = json.loads(_post_body)
		except JSONDecodeError:
			self._str = _post_body
		finally:
			return {**_get_params, **json_body}

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

	@property
	def request(self):
		return self._request


def convert_request(request):
	if not request.__dict__.get('arkfbp_request', None):
		_request = HttpRequest(request)
		request.__dict__.update(arkfbp_request=_request)

	return request.__dict__.get('arkfbp_request')
