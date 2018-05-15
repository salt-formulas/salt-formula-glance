# -*- coding: utf-8 -*-
'''
Managing Images in OpenStack Glance
===================================
'''
# Import python libs
import logging
import time


# Import OpenStack libs
def __virtual__():
    return 'glancev2' if 'glancev2.image_list' in __salt__ else False


log = logging.getLogger(__name__)


def _glancev2_call(fname, *args, **kwargs):
    return __salt__['glancev2.{}'.format(fname)](*args, **kwargs)


def image_present(name, cloud_name, location, image_properties,
                  import_from_format='raw', timeout=30,
                  sleep_time=5, checksum=None):
    """
    Creates a task to import an image

    This state checks if an image is present and, if not, creates a task
    with import_type that would download an image from a remote location and
    upload it to Glance.
    After the task is created, its status is monitored. On success the state
    would check that an image is present and return its ID.

    Also, this state can update(add and replace) image properties,
    but !!It can't delete properties, that are already in state

    :param name: name of the image
    :param cloud_name: name of the cloud in cloud.yaml
    :param location: url link describing where to obtain image
    :param image_properties: Dict that contains params needed
           to create or update image.
           :param container_format:  Format of the container
           :param disk_format: Format of the disk
           :param protected: If true, image will not be deletable.
           :param tags: List of strings related to the image
           :param visibility: Scope of image accessibility.
                              Valid values: public, private, community, shared
    :param import_from_format: (optional) Format to import the image from
    :param timeout: (optional) Time for task to download image
    :param sleep_time: (optional) Timer countdown
    :param checksum: (optional) checksum of the image to verify it
    """
    try:
        exact_image = _glancev2_call(
            'image_get_details', name=name, cloud_name=cloud_name
        )
    except Exception as e:
        if 'ResourceNotFound' in repr(e):
            image_properties['name'] = name
            task_params = {"import_from": location,
                           "import_from_format": import_from_format,
                           "image_properties": image_properties
                           }
            # Try create task
            try:
                task = _glancev2_call(
                    'task_create', task_type='import', task_input=task_params,
                    cloud_name=cloud_name
                )
            except Exception as e:
                log.error(
                    'Glance image create failed on create task with {}'.format(
                        e)
                )
                return _create_failed(name, 'image_task')
            while timeout > 0:
                if task['status'] == 'success':
                    break
                elif task['status'] == 'failure':
                    log.error('Glance task failed to complete')
                    return _create_failed(name, 'image')
                else:
                    timeout -= sleep_time
                    time.sleep(sleep_time)
                    # Check task status again
                    try:
                        task = _glancev2_call(
                            'task_show', task_id=task['id'],
                            cloud_name=cloud_name
                        )
                    except Exception as e:
                        log.error(
                            'Glance failed to check '
                            'task status with {}'.format(e)
                        )
                        return _create_failed(name, 'image_task')
            if timeout <= 0 and task['status'] != 'success':
                log.error(
                    'Glance task failed to import '
                    'image for given amount of time'
                )
                return _create_failed(name, 'image')
            # Task successfully finished
            # and now check that is created the image

            image = _glancev2_call(
                'image_list', name=name, cloud_name=cloud_name
            )['images'][0]

            if not image:
                return _create_failed(name, 'image')

            resp = _created(name, 'image', image)

            if checksum:
                if image['status'] == 'active':
                    if 'checksum' not in image:
                        log.error(
                            'Glance image. No checksum for image.'
                            'Image status is active'
                        )
                        return _create_failed(name, 'image')
                    if image['checksum'] != checksum:
                        log.error(
                            'Glance image create failed since '
                            'image_checksum should be '
                            '{} but it is {}'.format(checksum,
                                                     image['checksum'])
                        )
                        return _create_failed(name, 'image')

                elif image['status'] in ['saving', 'queued']:
                    resp['comment'] = resp['comment'] \
                                      + " checksum couldn't be verified, " \
                                        "since status is not active"
            return resp
        if 'MultipleResourcesFound' in repr(e):
            return _find_failed(name, 'image')
    to_change = []
    for prop in image_properties:
        path = prop.replace('~', '~0').replace('/', '~1')
        if prop in exact_image:
            if exact_image[prop] != image_properties[prop]:
                to_change.append({
                    'op': 'replace',
                    'path': '/{}'.format(path),
                    'value': image_properties[prop]
                })
        else:
            to_change.append({
                'op': 'add',
                'path': '/{}'.format(path),
                'value': image_properties[prop]
            })
    if to_change:
        try:
            resp = _glancev2_call(
                'image_update', name=name,
                properties=to_change, cloud_name=cloud_name,
            )
        except Exception as e:
            log.error('Glance image update failed with {}'.format(e))
            return _update_failed(name, 'image')
        return _updated(name, 'image', resp)
    return _no_changes(name, 'image')


def image_absent(name, cloud_name):
    try:
        image = _glancev2_call(
            'image_get_details', name=name, cloud_name=cloud_name
        )
    except Exception as e:
        if 'ResourceNotFound' in repr(e):
            return _absent(name, 'image')
        if 'MultipleResourcesFound' in repr(e):
            return _find_failed(name, 'image')
    try:
        _glancev2_call(
            'image_delete', name=name, cloud_name=cloud_name
        )
    except Exception as e:
        log.error('Glance image delete failed with {}'.format(e))
        return _delete_failed(name, 'image')
    return _deleted(name, 'image')


def _created(name, resource, resource_definition):
    changes_dict = {
        'name': name,
        'changes': resource_definition,
        'result': True,
        'comment': '{}{} created'.format(resource, name)
    }
    return changes_dict


def _updated(name, resource, resource_definition):
    changes_dict = {
        'name': name,
        'changes': resource_definition,
        'result': True,
        'comment': '{}{} updated'.format(resource, name)
    }
    return changes_dict


def _no_changes(name, resource):
    changes_dict = {
        'name': name,
        'changes': {},
        'result': True,
        'comment': '{}{} is in desired state'.format(resource, name)
    }
    return changes_dict


def _deleted(name, resource):
    changes_dict = {
        'name': name,
        'changes': {},
        'result': True,
        'comment': '{}{} removed'.format(resource, name)
    }
    return changes_dict


def _absent(name, resource):
    changes_dict = {'name': name,
                    'changes': {},
                    'comment': '{0} {1} not present'.format(resource, name),
                    'result': True}
    return changes_dict


def _delete_failed(name, resource):
    changes_dict = {'name': name,
                    'changes': {},
                    'comment': '{0} {1} failed to delete'.format(resource,
                                                                 name),
                    'result': False}
    return changes_dict


def _create_failed(name, resource):
    changes_dict = {'name': name,
                    'changes': {},
                    'comment': '{0} {1} failed to create'.format(resource,
                                                                 name),
                    'result': False}
    return changes_dict


def _update_failed(name, resource):
    changes_dict = {'name': name,
                    'changes': {},
                    'comment': '{0} {1} failed to update'.format(resource,
                                                                 name),
                    'result': False}
    return changes_dict


def _find_failed(name, resource):
    changes_dict = {
        'name': name,
        'changes': {},
        'comment': '{0} {1} found multiple {0}'.format(resource, name),
        'result': False,
    }
    return changes_dict
