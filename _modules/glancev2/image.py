try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import hashlib

from glancev2.common import send, get_raw_client, get_by_name_or_uuid

RESOURCE_LIST_KEY = 'images'


@send('get')
def image_list(**kwargs):
    url = '/images?{}'.format(urlencode(kwargs))
    return url, {}


@send('post')
def image_create(**kwargs):
    url = '/images'
    return url, {'json': kwargs}


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('get')
def image_get_details(image_id, **kwargs):
    url = '/images/{}'.format(image_id)
    return url, {}


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('patch')
def image_update(image_id, properties, **kwargs):
    url = '/images/{}'.format(image_id)
    headers = {
        'Content-Type': 'application/openstack-images-v2.1-json-patch',
    }
    return url, {'json': properties, 'headers': headers}


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('delete')
def image_delete(image_id, **kwargs):
    url = '/images/{}'.format(image_id)
    return url, {}


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('post')
def image_deactivate(image_id, **kwargs):
    url = '/images/{}/actions/deactivate'.format(image_id)
    return url, {}


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('post')
def image_reactivate(image_id, **kwargs):
    url = '/images/{}/actions/reactivate'.format(image_id)
    return url, {}


class StreamingDownloader(object):

    def __init__(self, adapter, image_id, chunksize):
        self.hasher = hashlib.new('md5')
        self.chunksize = chunksize

        resp = adapter.get('/images/{}/file'.format(image_id),
                           stream=True)
        if resp.status_code != 200:
            raise Exception('Invalid response code: %s' % resp.status_code)

        self._request = resp

    def __iter__(self):
        for chunk in self._request.iter_content(chunk_size=self.chunksize):
            self.hasher.update(chunk)
            yield chunk

    def validate(self):
        return self.hasher.hexdigest() == self._request.headers['Content-Md5']


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
def image_data_download(image_id, file_name, **kwargs):
    cloud_name = kwargs.pop('cloud_name')
    adapter = get_raw_client(cloud_name)
    downloader = StreamingDownloader(adapter, image_id, 1024 * 1024)
    with open(file_name, 'wb') as f:
        for chunk in downloader:
            f.write(chunk)
    return downloader.validate()


@get_by_name_or_uuid(image_list, RESOURCE_LIST_KEY)
@send('put')
def image_data_upload(image_id, file_name, **kwargs):
    url = '/images/{}/file'.format(image_id)
    headers = {'Content-Type': 'application/octet-stream '}
    with open(file_name, 'rb') as f:
        data = f.readlines()
    return url, {'json': data, 'headers': headers}
