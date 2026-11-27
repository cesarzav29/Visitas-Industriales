from django import template

from periodos.services import obtener_periodo_abierto


register = template.Library()


@register.simple_tag
def periodo_abierto():
    return obtener_periodo_abierto()
