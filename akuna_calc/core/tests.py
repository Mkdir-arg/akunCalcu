from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class BaseTemplateSelect2HelperTest(SimpleTestCase):
    def test_base_exposes_shared_select2_helper_and_styles(self):
        request = RequestFactory().get('/')
        request.user = SimpleNamespace(
            username='tester',
            is_authenticated=True,
            is_superuser=True,
            pk=None,
        )

        html = render_to_string(
            'core/base.html',
            {
                'sidebar_modules': [],
                'user_role_label': 'Admin',
                'user_access_summary': 'Acceso total',
            },
            request=request,
        )

        self.assertIn('window.AkunSelect2 = {', html)
        self.assertIn('function initAkunSelect2(target, customOptions)', html)
        self.assertIn('function reinitAkunSelect2(target, customOptions)', html)
        self.assertIn('initAkunSelect2(document);', html)
        self.assertIn('.select2-container--classic .select2-selection--single', html)
