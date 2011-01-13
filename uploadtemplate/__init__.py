def _is_disabled():
    # Import the current Django settings
    from django.conf import settings

    # Get the value from settings
    disable_upload = getattr(settings, 'UPLOADTEMPLATE_DISABLE_UPLOAD', False)
    # If it is a callable, return its return value.
    if callable(disable_upload):
        return disable_upload()
    # Else, return whatever we got
    return disable_upload
