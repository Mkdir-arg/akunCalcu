from pathlib import Path

from django.template import Template
from django.test import SimpleTestCase


class TemplatesContabilidadTests(SimpleTestCase):
    """La app no está instalada ni enrutada en el proyecto: se verifica que los templates compilen."""

    def test_templates_compilan(self):
        base = Path(__file__).parent / 'templates' / 'contabilidad'
        for name in ('plan_cuentas', 'estado_resultados', 'balance_general'):
            Template((base / f'{name}.html').read_text(encoding='utf-8'))
