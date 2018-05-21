try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
from glancev2.common import send


@send('post')
def task_create(task_type, task_input, **kwargs):
    url = '/tasks'
    json = {
        'type': task_type,
        'input': task_input
    }
    return url, {'json': json}


@send('get')
def task_list(**kwargs):
    url = '/tasks?{}'.format(urlencode(kwargs))
    return url, {}


@send('get')
def task_show(task_id, **kwargs):
    url = '/tasks/{}'.format(task_id)
    return url, {}
