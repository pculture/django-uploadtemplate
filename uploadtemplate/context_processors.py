from uploadtemplate.models import Theme


def theme(request):
	try:
		theme = Theme.objects.get_default()
	except Theme.DoesNotExist:
		theme = None
	return {
		'uploadtemplate_current_theme': theme
	}