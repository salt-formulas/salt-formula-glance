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
    endpoint_type = connection_args.get('connection_endpoint_type', 'internal')
    g_endpoint = __salt__['keystoneng.endpoint_get']('glance', profile=profile, interface=endpoint_type)
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
