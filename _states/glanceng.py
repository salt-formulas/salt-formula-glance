# -*- coding: utf-8 -*-
'''
Managing Images in OpenStack Glance
===================================
'''
# Import python libs
from __future__ import absolute_import
import logging
import time

# Import OpenStack libs
try:
    from keystoneclient.exceptions import \
        Unauthorized as kstone_Unauthorized
    HAS_KEYSTONE = True
except ImportError:
    try:
        from keystoneclient.apiclient.exceptions import \
            Unauthorized as kstone_Unauthorized
        HAS_KEYSTONE = True
    except ImportError:
        HAS_KEYSTONE = False

try:
    from glanceclient.exc import \
        HTTPUnauthorized as glance_Unauthorized
    HAS_GLANCE = True
except ImportError:
    HAS_GLANCE = False

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only load if dependencies are loaded
    '''
    return HAS_KEYSTONE and HAS_GLANCE


def _find_image(name, profile=None):
    '''
    Tries to find image with given name, returns
        - image, 'Found image <name>'
        - None, 'No such image found'
        - False, 'Found more than one image with given name'
    '''
    try:
        images = __salt__['glance.image_list'](name=name, profile=profile)
    except kstone_Unauthorized:
        return False, 'keystoneclient: Unauthorized'
    except glance_Unauthorized:
        return False, 'glanceclient: Unauthorized'
    log.debug('Got images: {0}'.format(images))

    if type(images) is dict and len(images) == 1 and 'images' in images:
        images = images['images']

    images_list = list(images.values()) if type(images) is dict else images

    if len(images_list) == 0:
        return None, 'No image with name "{0}"'.format(name)
    elif len(images_list) == 1:
        return images_list[0], 'Found image {0}'.format(name)
    elif len(images_list) > 1:
        return False, 'Found more than one image with given name'
    else:
        raise NotImplementedError


def image_present(name, profile=None, visibility='public', protected=None,
        checksum=None, location=None, disk_format='raw', wait_for=None,
        timeout=30):
    '''
    Checks if given image is present with properties
    set as specified.
    An image should got through the stages 'queued', 'saving'
    before becoming 'active'. The attribute 'checksum' can
    only be checked once the image is active.
    If you don't specify 'wait_for' but 'checksum' the function
    will wait for the image to become active before comparing
    checksums. If you don't specify checksum either the function
    will return when the image reached 'saving'.
    The default timeout for both is 30 seconds.
    Supported properties:
      - profile (string)
      - visibility ('public' or 'private')
      - protected (bool)
      - checksum (string, md5sum)
      - location (URL, to copy from)
      - disk_format ('raw' (default), 'vhd', 'vhdx', 'vmdk', 'vdi', 'iso',
        'qcow2', 'aki', 'ari' or 'ami')
    '''
    ret = {'name': name,
            'changes': {},
            'result': True,
            'comment': '',
            }
    acceptable = ['queued', 'saving', 'active']
    if wait_for is None and checksum is None:
        wait_for = 'saving'
    elif wait_for is None and checksum is not None:
        wait_for = 'active'

    # Just pop states until we reach the
    # first acceptable one:
    while len(acceptable) > 1:
        if acceptable[0] == wait_for:
            break
        else:
            acceptable.pop(0)

    image, msg = _find_image(name, profile)
    if image is False:
        if __opts__['test']:
            ret['result'] = None
        else:
            ret['result'] = False
        ret['comment'] = msg
        return ret
    log.debug(msg)
    # No image yet and we know where to get one
    if image is None and location is not None:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'glance.image_present would ' \
                'create an image from {0}'.format(location)
            return ret
        image = __salt__['glance.image_create'](name=name, profile=profile,
            protected=protected, visibility=visibility,
            location=location, disk_format=disk_format)
        log.debug('Created new image:\n{0}'.format(image))
        ret['changes'] = {
            name:
                {
                    'new':
                        {
                        'id': image['id']
                        },
                    'old': None
                }
            }
        timer = timeout
        # Kinda busy-loopy but I don't think the Glance
        # API has events we can listen for
        while timer > 0:
            if 'status' in image and \
                    image['status'] in acceptable:
                log.debug('Image {0} has reached status {1}'.format(
                    image['name'], image['status']))
                break
            else:
                timer -= 5
                time.sleep(5)
                image, msg = _find_image(name, profile)
                if not image:
                    ret['result'] = False
                    ret['comment'] += 'Created image {0} '.format(
                        name) + ' vanished:\n' + msg
                    return ret
        if timer <= 0 and image['status'] not in acceptable:
            ret['result'] = False
            ret['comment'] += 'Image didn\'t reach an acceptable '+\
                    'state ({0}) before timeout:\n'.format(acceptable)+\
                    '\tLast status was "{0}".\n'.format(image['status'])

    # There's no image but where would I get one??
    elif location is None:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = 'No location to copy image from specified,\n' +\
                         'glance.image_present would not create one'
        else:
            ret['result'] = False
            ret['comment'] = 'No location to copy image from specified,\n' +\
                         'not creating a new image.'
        return ret

    # If we've created a new image also return its last status:
    if name in ret['changes']:
        ret['changes'][name]['new']['status'] = image['status']

    if visibility:
        if image['visibility'] != visibility:
            old_value = image['visibility']
            if not __opts__['test']:
                image = __salt__['glance.image_update'](
                    id=image['id'], visibility=visibility)
            # Check if image_update() worked:
            if image['visibility'] != visibility:
                if not __opts__['test']:
                    ret['result'] = False
                elif __opts__['test']:
                    ret['result'] = None
                ret['comment'] += '"visibility" is {0}, '\
                    'should be {1}.\n'.format(image['visibility'],
                        visibility)
            else:
                if 'new' in ret['changes']:
                    ret['changes']['new']['visibility'] = visibility
                else:
                    ret['changes']['new'] = {'visibility': visibility}
                if 'old' in ret['changes']:
                    ret['changes']['old']['visibility'] = old_value
                else:
                    ret['changes']['old'] = {'visibility': old_value}
        else:
            ret['comment'] += '"visibility" is correct ({0}).\n'.format(
                visibility)
    if protected is not None:
        if not isinstance(protected, bool) or image['protected'] ^ protected:
            if not __opts__['test']:
                ret['result'] = False
            else:
                ret['result'] = None
            ret['comment'] += '"protected" is {0}, should be {1}.\n'.format(
                image['protected'], protected)
        else:
            ret['comment'] += '"protected" is correct ({0}).\n'.format(
                protected)
    if 'status' in image and checksum:
        if image['status'] == 'active':
            if 'checksum' not in image:
                # Refresh our info about the image
                image = __salt__['glance.image_show'](image['id'])
            if 'checksum' not in image:
                if not __opts__['test']:
                    ret['result'] = False
                else:
                    ret['result'] = None
                ret['comment'] += 'No checksum available for this image:\n' +\
                        '\tImage has status "{0}".'.format(image['status'])
            elif image['checksum'] != checksum:
                if not __opts__['test']:
                    ret['result'] = False
                else:
                    ret['result'] = None
                ret['comment'] += '"checksum" is {0}, should be {1}.\n'.format(
                    image['checksum'], checksum)
            else:
                ret['comment'] += '"checksum" is correct ({0}).\n'.format(
                    checksum)
        elif image['status'] in ['saving', 'queued']:
            ret['comment'] += 'Checksum won\'t be verified as image ' +\
                'hasn\'t reached\n\t "status=active" yet.\n'
    log.debug('glance.image_present will return: {0}'.format(ret))
    return ret


def image_import(name, profile=None, visibility='public', protected=False,
                 location=None, import_from_format='raw', disk_format='raw',
                 container_format='bare', tags=None,
                 checksum=None, timeout=30):
    """
    Creates a task to import an image

    This state checks if an image is present and, if not, creates a task
    with import_type that would download an image from a remote location and
    upload it to Glance.
    After the task is created, its status is monitored. On success the state
    would check that an image is present and return its ID.

    *Important*: This state is supposed to work only with Glance V2 API as
                 opposed to the image_present state that is compatible only
                 with Glance V1.

    :param name: Name of an image
    :param profile: Authentication profile
    :param visibility: Scope of image accessibility.
                       Valid values: public, private, community, shared
    :param protected: If true, image will not be deletable.
    :param location: a URL where Glance can get the image data
    :param import_from_format: Format to import the image from
    :param disk_format: Format of the disk
    :param container_format: Format of the container
    :param tags: List of strings related to the image
    :param checksum: Checksum of the image to import, it would be used to
                     validate the checksum of a newly created image
    :param timeout: Time to wait for an import task to succeed
    """

    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Image "{0}" already exists'.format(name)}
    tags = tags or []

    image, msg = _find_image(name, profile)
    log.debug(msg)
    if image:
        return ret
    elif image is False:
        if __opts__['test']:
            ret['result'] = None
        else:
            ret['result'] = False
        ret['comment'] = msg
        return ret
    else:
        if __opts__['test']:
            ret['result'] = None
            ret['comment'] = ("glanceng.image_import would create an image "
                              "from {0}".format(location))
            return ret

        image_properties = {"container_format": container_format,
                            "disk_format": disk_format,
                            "name": name,
                            "protected": protected,
                            "tags": tags,
                            "visibility": visibility
                            }
        task_params = {"import_from": location,
                       "import_from_format": import_from_format,
                       "image_properties": image_properties
                       }

        task = __salt__['glanceng.task_create'](
            task_type='import', profile=profile,
            input_params=task_params)
        task_id = task['id']
        log.debug('Created new task:\n{0}'.format(task))
        ret['changes'] = {
            name:
                {
                    'new':
                        {
                            'task_id': task_id
                        },
                    'old': None
                }
            }

        # Wait for the task to complete
        timer = timeout
        while timer > 0:
            if 'status' in task and task['status'] == 'success':
                log.debug('Task {0} has successfully completed'.format(
                    task_id))
                break
            elif 'status' in task and task['status'] == 'failure':
                msg = "Task {0} has failed".format(task_id)
                ret['result'] = False
                ret['comment'] = msg
                return ret
            else:
                timer -= 5
                time.sleep(5)
                existing_tasks = __salt__['glanceng.task_list'](profile)
                if task_id not in existing_tasks:
                    ret['result'] = False
                    ret['comment'] += 'Created task {0} '.format(
                        task_id) + ' vanished:\n' + msg
                    return ret
                else:
                    task = existing_tasks[task_id]
        if timer <= 0 and task['status'] != 'success':
            ret['result'] = False
            ret['comment'] = ('Task {0} did not reach state success before '
                              'the timeout:\nLast status was '
                              '"{1}".\n'.format(task_id, task['status']))
            return ret

        # The import task has successfully completed. Now, let's check that it
        # created the image.
        image, msg = _find_image(name, profile)
        if not image:
            ret['result'] = False
            ret['comment'] = msg
        else:
            ret['changes'][name]['new']['image_id'] = image['id']
            ret['changes'][name]['new']['image_status'] = image['status']
            ret['comment'] = ("Image {0} was successfully created by task "
                              "{1}".format(image['id'], task_id))
            if checksum:
                if image['status'] == 'active':
                    if 'checksum' not in image:
                        # Refresh our info about the image
                        image = __salt__['glance.image_show'](image['id'])
                    if 'checksum' not in image:
                        if not __opts__['test']:
                            ret['result'] = False
                        else:
                            ret['result'] = None
                        ret['comment'] += (
                            "No checksum available for this image:\n"
                            "Image has status '{0}'.".format(image['status']))
                    elif image['checksum'] != checksum:
                        if not __opts__['test']:
                            ret['result'] = False
                        else:
                            ret['result'] = None
                        ret['comment'] += ("'checksum' is {0}, should be "
                                           "{1}.\n".format(image['checksum'],
                                                           checksum))
                    else:
                        ret['comment'] += (
                            "'checksum' is correct ({0}).\n".format(checksum))
                elif image['status'] in ['saving', 'queued']:
                    ret['comment'] += (
                        "Checksum will not be verified as image has not "
                        "reached 'status=active' yet.\n")
        log.debug('glance.image_present will return: {0}'.format(ret))
        return ret
