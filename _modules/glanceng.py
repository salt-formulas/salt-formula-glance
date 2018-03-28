# -*- coding: utf-8 -*-
"""
Module extending the salt.modules.glance modules.

This module adds functionality for managing Glance V2 tasks by exposing the
following functions:
  - task_create
  - task_show
  - task_list

:optdepends:    - glanceclient Python adapter
:configuration: This module is not usable until the following are specified
    either in a pillar or in the minion's config file::

        keystone.user: admin
        keystone.password: verybadpass
        keystone.tenant: admin
        keystone.insecure: False   #(optional)
        keystone.auth_url: 'http://127.0.0.1:5000/v2.0/'

    If configuration for multiple openstack accounts is required, they can be
    set up as different configuration profiles:
    For example::

        openstack1:
          keystone.user: admin
          keystone.password: verybadpass
          keystone.tenant: admin
          keystone.auth_url: 'http://127.0.0.1:5000/v2.0/'

        openstack2:
          keystone.user: admin
          keystone.password: verybadpass
          keystone.tenant: admin
          keystone.auth_url: 'http://127.0.0.2:5000/v2.0/'

    With this configuration in place, any of the glance functions can
    make use of a configuration profile by declaring it explicitly.
    For example::

        salt '*' glance.image_list profile=openstack1
"""

# Import Python libs
from __future__ import absolute_import
import logging
import pprint
import re

# Import salt libs
from salt.exceptions import SaltInvocationError

from salt.version import (
    __version__,
    SaltStackVersion
    )

from salt.utils import warn_until

# is there not SaltStackVersion.current() to get
# the version of the salt running this code??
_version_ary = __version__.split('.')
CUR_VER = SaltStackVersion(_version_ary[0], _version_ary[1])
BORON = SaltStackVersion.from_name('Boron')

# pylint: disable=import-error
HAS_GLANCE = False
try:
    from glanceclient import client
    from glanceclient import exc
    HAS_GLANCE = True
except ImportError:
    pass


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load this module if glance
    is installed on this minion.
    '''
    if not HAS_GLANCE:
        return False, ("The glance execution module cannot be loaded: "
                       "the glanceclient python library is not available.")
    return True


__opts__ = {}


def _auth(profile=None, api_version=2, **connection_args):
    '''
    Set up glance credentials, returns
    `glanceclient.client.Client`. Optional parameter
    "api_version" defaults to 2.

    Only intended to be used within glance-enabled modules
    '''

    kstone = __salt__['keystoneng.auth'](profile, **connection_args)
    g_endpoint = __salt__['keystoneng.endpoint_get']('glance', profile=profile)
    glance_client = client.Client(api_version, session=kstone.session, endpoint=g_endpoint.get('url'))
    return glance_client


def _validate_image_params(visibility=None, container_format='bare',
                           disk_format='raw', tags=None, **kwargs):
    # valid options for "visibility":
    v_list = ['public', 'private', 'shared', 'community']
    # valid options for "container_format":
    cf_list = ['ami', 'ari', 'aki', 'bare', 'ovf']
    # valid options for "disk_format":
    df_list = ['ami', 'ari', 'aki', 'vhd', 'vmdk',
               'raw', 'qcow2', 'vdi', 'iso']

    if visibility is not None:
        if visibility not in v_list:
            raise SaltInvocationError('"visibility" needs to be one ' +
                                      'of the following: {0}'.format(
                                          ', '.join(v_list)))
    if container_format not in cf_list:
        raise SaltInvocationError('"container_format" needs to be ' +
                                  'one of the following: {0}'.format(
                                      ', '.join(cf_list)))
    if disk_format not in df_list:
        raise SaltInvocationError('"disk_format" needs to be one ' +
                                  'of the following: {0}'.format(
                                      ', '.join(df_list)))
    if tags:
        if not isinstance(tags, list):
            raise SaltInvocationError('Incorrect input type for the {0} '
                                      'parameter: expected: {1}, '
                                      'got {2}'.format("tags", list,
                                                       type(tags)))


def _validate_task_params(task_type, input_params):
    # Only import tasks are currently supported
    # TODO(eezhova): Add support for "export" and "clone" task types
    valid_task_types = ["import", ]

    import_required_params = {"import_from", "import_from_format",
                              "image_properties"}

    if task_type not in valid_task_types:
        raise SaltInvocationError("'task_type' must be one of the following: "
                                  "{0}".format(', '.join(valid_task_types)))

    if task_type == "import":
        valid_import_from_formats = ['ami', 'ari', 'aki', 'vhd', 'vmdk',
                                     'raw', 'qcow2', 'vdi', 'iso']
        missing_params = import_required_params - set(input_params.keys())
        if missing_params:
            raise SaltInvocationError(
                "Missing the following task parameters for the 'import' task: "
                "{0}".format(', '.join(missing_params)))

        import_from = input_params['import_from']
        import_from_format = input_params['import_from_format']
        image_properties = input_params['image_properties']
        if not import_from.startswith(('http://', 'https://')):
            raise SaltInvocationError("Only non-local sources of image data "
                                      "are supported.")
        if import_from_format not in valid_import_from_formats:
            raise SaltInvocationError(
                "'import_from_format' needs to be one of the following: "
                "{0}".format(', '.join(valid_import_from_formats)))
        _validate_image_params(**image_properties)


def task_create(task_type, profile=None, input_params=None):
    """
    Create a Glance V2 task of a given type

    :param task_type: Task type
    :param profile: Authentication profile
    :param input_params: Dictionary with input parameters for a task
    :return: Dictionary with created task's parameters
    """
    g_client = _auth(profile, api_version=2)
    log.debug(
        'Task type: {}\nInput params: {}'.format(task_type, input_params)
    )
    task = g_client.tasks.create(type=task_type, input=input_params)
    log.debug("Created task: {}".format(dict(task)))
    created_task = task_show(task.id, profile=profile)
    return created_task


def task_show(task_id, profile=None):
    """
    Show a Glance V2 task

    :param task_id: ID of a task to show
    :param profile: Authentication profile
    :return: Dictionary with created task's parameters
    """
    g_client = _auth(profile)
    ret = {}
    try:
        task = g_client.tasks.get(task_id)
    except exc.HTTPNotFound:
        return {
            'result': False,
            'comment': 'No task with ID {0}'.format(task_id)
        }
    pformat = pprint.PrettyPrinter(indent=4).pformat
    log.debug('Properties of task {0}:\n{1}'.format(
        task_id, pformat(task)))

    schema = image_schema(schema_type='task', profile=profile)
    if len(schema.keys()) == 1:
        schema = schema['task']
    for key in schema.keys():
        if key in task:
            ret[key] = task[key]
    return ret


def task_list(profile=None):
    """
    List Glance V2 tasks

    :param profile: Authentication profile
    :return: Dictionary with existing tasks
    """
    g_client = _auth(profile)
    ret = {}
    tasks = g_client.tasks.list()
    schema = image_schema(schema_type='task', profile=profile)
    if len(schema.keys()) == 1:
        schema = schema['task']
    for task in tasks:
        task_dict = {}
        for key in schema.keys():
            if key in task:
                task_dict[key] = task[key]
        ret[task['id']] = task_dict
    return ret


def get_image_owner_id(name, profile=None):
    """
    Mine function to get image owner

    :param name: Name of the image
    :param profile: Authentication profile
    :return: Image owner ID or [] if image is not found
    """
    g_client = _auth(profile)
    image_id = None
    for image in g_client.images.list():
        if image.name == name:
            image_id = image.id
            continue
    if not image_id:
        return []
    try:
        image = g_client.images.get(image_id)
    except exc.HTTPNotFound:
        return []
    return image['owner']


def image_schema(schema_type='image', profile=None):
    '''
    Returns names and descriptions of the schema "image"'s
    properties for this profile's instance of glance

    CLI Example:

    .. code-block:: bash

        salt '*' glance.image_schema
    '''
    return schema_get(schema_type, profile)


def schema_get(name, profile=None):
    '''
    Known valid names of schemas are:
      - image
      - images
      - member
      - members

    CLI Example:

    .. code-block:: bash

        salt '*' glance.schema_get name=f16-jeos
    '''
    g_client = _auth(profile)
    pformat = pprint.PrettyPrinter(indent=4).pformat
    schema_props = {}
    for prop in g_client.schemas.get(name).properties:
        schema_props[prop.name] = prop.description
    log.debug('Properties of schema {0}:\n{1}'.format(
        name, pformat(schema_props)))
    return {name: schema_props}

def image_list(id=None, profile=None, name=None):  # pylint: disable=C0103
    '''
    Return a list of available images (glance image-list)

    CLI Example:

    .. code-block:: bash

        salt '*' glance.image_list
    '''
    #try:
    g_client = _auth(profile)
    #except kstone_exc.Unauthorized:
    #    return False
    #
    # I may want to use this code on Beryllium
    # until we got 2016.3.0 packages for Ubuntu
    # so please keep this code until Carbon!
    warn_until('Carbon', 'Starting in \'2016.3.0\' image_list() '
        'will return a list of images instead of a dictionary '
        'keyed with the images\' names.')
    if CUR_VER < BORON:
        ret = {}
    else:
        ret = []
    for image in g_client.images.list():
        if id is None and name is None:
            _add_image(ret, image)
        else:
            if id is not None and id == image.id:
                _add_image(ret, image)
                return ret
            if name == image.name:
                if name in ret and CUR_VER < BORON:
                    # Not really worth an exception
                    return {
                        'result': False,
                        'comment':
                            'More than one image with '
                            'name "{0}"'.format(name)
                        }
                _add_image(ret, image)
    log.debug('Returning images: {0}'.format(ret))
    return ret

def _add_image(collection, image):
    '''
    Add image to given dictionary
    '''
    image_prep = {
            'id': image.id,
            'name': image.name,
            'created_at': image.created_at,
            'file': image.file,
            'min_disk': image.min_disk,
            'min_ram': image.min_ram,
            'owner': image.owner,
            'protected': image.protected,
            'status': image.status,
            'tags': image.tags,
            'updated_at': image.updated_at,
            'visibility': image.visibility,
        }
    # Those cause AttributeErrors in Icehouse' glanceclient
    for attr in ['container_format', 'disk_format', 'size']:
        if attr in image:
            image_prep[attr] = image[attr]
    if type(collection) is dict:
        collection[image.name] = image_prep
    elif type(collection) is list:
        collection.append(image_prep)
    else:
        msg = '"collection" is {0}'.format(type(collection)) +\
            'instead of dict or list.'
        log.error(msg)
        raise TypeError(msg)
    return collection

def image_create(name, location=None, profile=None, visibility=None,
        container_format='bare', disk_format='raw', protected=None,
        copy_from=None, is_public=None):
    '''
    Create an image (glance image-create)

    CLI Example, old format:

    .. code-block:: bash

        salt '*' glance.image_create name=f16-jeos is_public=true \\
                 disk_format=qcow2 container_format=ovf \\
                 copy_from=http://berrange.fedorapeople.org/\
                    images/2012-02-29/f16-x86_64-openstack-sda.qcow2

    CLI Example, new format resembling Glance API v2:

    .. code-block:: bash

        salt '*' glance.image_create name=f16-jeos visibility=public \\
                 disk_format=qcow2 container_format=ovf \\
                 copy_from=http://berrange.fedorapeople.org/\
                    images/2012-02-29/f16-x86_64-openstack-sda.qcow2

    The parameter 'visibility' defaults to 'public' if neither
    'visibility' nor 'is_public' is specified.
    '''
    kwargs = {}
    # valid options for "visibility":
    v_list = ['public', 'private']
    # valid options for "container_format":
    cf_list = ['ami', 'ari', 'aki', 'bare', 'ovf']
    # valid options for "disk_format":
    df_list = ['ami', 'ari', 'aki', 'vhd', 'vmdk',
               'raw', 'qcow2', 'vdi', 'iso']
    # 'location' and 'visibility' are the parameters used in
    # Glance API v2. For now we have to use v1 for now (see below)
    # but this modules interface will change in Carbon.
    if copy_from is not None or is_public is not None:
        warn_until('Carbon', 'The parameters \'copy_from\' and '
            '\'is_public\' are deprecated and will be removed. '
            'Use \'location\' and \'visibility\' instead.')
    if is_public is not None and visibility is not None:
        raise SaltInvocationError('Must only specify one of '
            '\'is_public\' and \'visibility\'')
    if copy_from is not None and location is not None:
        raise SaltInvocationError('Must only specify one of '
            '\'copy_from\' and \'location\'')
    if copy_from is not None:
        kwargs['copy_from'] = copy_from
    else:
        kwargs['copy_from'] = location
    if is_public is not None:
        kwargs['is_public'] = is_public
    elif visibility is not None:
        if visibility not in v_list:
            raise SaltInvocationError('"visibility" needs to be one ' +
                'of the following: {0}'.format(', '.join(v_list)))
        elif visibility == 'public':
            kwargs['is_public'] = True
        else:
            kwargs['is_public'] = False
    else:
        kwargs['is_public'] = True
    if container_format not in cf_list:
        raise SaltInvocationError('"container_format" needs to be ' +
            'one of the following: {0}'.format(', '.join(cf_list)))
    else:
        kwargs['container_format'] = container_format
    if disk_format not in df_list:
        raise SaltInvocationError('"disk_format" needs to be one ' +
            'of the following: {0}'.format(', '.join(df_list)))
    else:
        kwargs['disk_format'] = disk_format
    if protected is not None:
        kwargs['protected'] = protected
    # Icehouse's glanceclient doesn't have add_location() and
    # glanceclient.v2 doesn't implement Client.images.create()
    # in a usable fashion. Thus we have to use v1 for now.
    g_client = _auth(profile, api_version=1)
    image = g_client.images.create(name=name, **kwargs)
    return image_show(image.id, profile=profile)

def image_delete(id=None, name=None, profile=None):  # pylint: disable=C0103
    '''
    Delete an image (glance image-delete)

    CLI Examples:

    .. code-block:: bash

        salt '*' glance.image_delete c2eb2eb0-53e1-4a80-b990-8ec887eae7df
        salt '*' glance.image_delete id=c2eb2eb0-53e1-4a80-b990-8ec887eae7df
        salt '*' glance.image_delete name=f16-jeos
    '''
    g_client = _auth(profile)
    image = {'id': False, 'name': None}
    if name:
        for image in g_client.images.list():
            if image.name == name:
                id = image.id  # pylint: disable=C0103
                continue
    if not id:
        return {
            'result': False,
            'comment':
                'Unable to resolve image id '
                'for name {0}'.format(name)
            }
    elif not name:
        name = image['name']
    try:
        g_client.images.delete(id)
    except exc.HTTPNotFound:
        return {
            'result': False,
            'comment': 'No image with ID {0}'.format(id)
            }
    except exc.HTTPForbidden as forbidden:
        log.error(str(forbidden))
        return {
            'result': False,
            'comment': str(forbidden)
            }
    return {
        'result': True,
        'comment': 'Deleted image \'{0}\' ({1}).'.format(name, id),
        }

def image_show(id=None, name=None, profile=None):  # pylint: disable=C0103
    '''
    Return details about a specific image (glance image-show)

    CLI Example:

    .. code-block:: bash

        salt '*' glance.image_show
    '''
    g_client = _auth(profile)
    ret = {}
    if name:
        for image in g_client.images.list():
            if image.name == name:
                id = image.id  # pylint: disable=C0103
                continue
    if not id:
        return {
            'result': False,
            'comment':
                'Unable to resolve image ID '
                'for name \'{0}\''.format(name)
            }
    try:
        image = g_client.images.get(id)
    except exc.HTTPNotFound:
        return {
            'result': False,
            'comment': 'No image with ID {0}'.format(id)
            }
    pformat = pprint.PrettyPrinter(indent=4).pformat
    log.debug('Properties of image {0}:\n{1}'.format(
        image.name, pformat(image)))
    ret_details = {}
    # I may want to use this code on Beryllium
    # until we got 2016.3.0 packages for Ubuntu
    # so please keep this code until Carbon!
    warn_until('Carbon', 'Starting with \'2016.3.0\' image_show() '
            'will stop wrapping the returned image in another '
            'dictionary.')
    if CUR_VER < BORON:
        ret[image.name] = ret_details
    else:
        ret = ret_details
    schema = image_schema(profile=profile)
    if len(schema.keys()) == 1:
        schema = schema['image']
    for key in schema.keys():
        if key in image:
            ret_details[key] = image[key]
    return ret

def image_update(id=None, name=None, profile=None, **kwargs):  # pylint: disable=C0103
    '''
    Update properties of given image.
    Known to work for:
    - min_ram (in MB)
    - protected (bool)
    - visibility ('public' or 'private')

    CLI Example:

    .. code-block:: bash

        salt '*' glance.image_update id=c2eb2eb0-53e1-4a80-b990-8ec887eae7df
        salt '*' glance.image_update name=f16-jeos
    '''
    if id:
        image = image_show(id=id, profile=profile)
        if 'result' in image and not image['result']:
            return image
        elif len(image) == 1:
            image = image.values()[0]
    elif name:
        img_list = image_list(name=name, profile=profile)
        if img_list is dict and 'result' in img_list:
            return img_list
        elif len(img_list) == 0:
            return {
                'result': False,
                'comment':
                    'No image with name \'{0}\' '
                    'found.'.format(name)
                }
        elif len(img_list) == 1:
            try:
                image = img_list[0]
            except KeyError:
                image = img_list[name]
    else:
        raise SaltInvocationError
    log.debug('Found image:\n{0}'.format(image))
    to_update = {}
    for key, value in kwargs.items():
        if key.startswith('_'):
            continue
        if key not in image or image[key] != value:
            log.debug('add <{0}={1}> to to_update'.format(key, value))
            to_update[key] = value
    g_client = _auth(profile)
    updated = g_client.images.update(image['id'], **to_update)
    # I may want to use this code on Beryllium
    # until we got 2016.3.0 packages for Ubuntu
    # so please keep this code until Carbon!
    warn_until('Carbon', 'Starting with \'2016.3.0\' image_update() '
            'will stop wrapping the returned, updated image in '
            'another dictionary.')
    if CUR_VER < BORON:
        updated = {updated.name: updated}
    return updated

def _item_list(profile=None):
    '''
    Template for writing list functions
    Return a list of available items (glance items-list)

    CLI Example:

    .. code-block:: bash

        salt '*' glance.item_list
    '''
    g_client = _auth(profile)
    ret = []
    for item in g_client.items.list():
        ret.append(item.__dict__)
        #ret[item.name] = {
        #        'name': item.name,
        #    }
    return ret
