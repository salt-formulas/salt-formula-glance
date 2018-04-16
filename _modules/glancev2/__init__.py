try:
    import os_client_config
    from keystoneauth1 import exceptions as ka_exceptions
    REQUIREMENTS_MET = True
except ImportError:
    REQUIREMENTS_MET = False

from glancev2 import image
from glancev2 import task

image_create = image.image_create
image_delete = image.image_delete
image_deactivate = image.image_deactivate
image_reactivate = image.image_reactivate
image_list = image.image_list
image_update = image.image_update
image_download = image.image_data_download
image_get_details = image.image_get_details
task_list = task.task_list
task_create = task.task_create
task_show = task.task_show

__all__ = (
    'image_update', 'image_create', 'image_list', 'image_delete', 'task_show',
    'image_download', 'task_create', 'task_list', 'image_get_details',
    'image_deactivate', 'image_reactivate'
)


def __virtual__():
    """Only load glanceng if requirements are available."""
    if REQUIREMENTS_MET:
        return 'glancev2'
    else:
        return False, ("The glanceng execution module cannot be loaded: "
                       "os_client_config or keystoneauth are unavailable.")
