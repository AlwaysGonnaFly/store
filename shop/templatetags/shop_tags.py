from django import template

register = template.Library()


@register.filter(name='get_ids_of_good_params')
def get_ids_of_good_params(request_get):
    ids = []
    for p in request_get.split('%'):
        try:
            ids.append(int(p))
        except ValueError:
            continue
    return ids
