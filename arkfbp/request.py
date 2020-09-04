import json
from json.decoder import JSONDecodeError
from django.core.handlers.wsgi import WSGIRequest


def process_request(request):
	if not hasattr(request, 'extra_data'):
		request.extra_data = {}

	if not hasattr(request, 'data') and not hasattr(request, 'str'):
		request.data, request.str = _extract(request)

	return request


def _extract(request: WSGIRequest):
	"""
	Parse the request GET and POST data and
	merge it together.
	"""
	data_str = ''

	_get_params = request.GET.dict()
	_post_params = request.POST.dict()

	# 1）`body`为`form-data`、`application/x-www-form-urlencoded`格式数据
	if _post_params:
		data = {**_get_params, **_post_params}
		return data, data_str

	# 2）`body`为`json`、`text`等其他形式数据
	_post_body = request.body
	if not _post_body:
		data = {**_get_params}
		return data, data_str

	try:
		json_body = {}
		json_body = json.loads(_post_body)
	except JSONDecodeError:
		data_str = _post_body
	finally:
		data = {**_get_params, **json_body}
	return data, data_str
