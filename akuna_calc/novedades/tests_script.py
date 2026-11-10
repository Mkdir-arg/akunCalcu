"""Tests del script de la GitHub Action (.github/scripts/novedad_borrador.py).

En el contenedor no existe .github/: ahí se saltean.
"""
import importlib.util
from pathlib import Path
from unittest import SkipTest, mock

from django.conf import settings
from django.test import SimpleTestCase

SCRIPT = Path(settings.BASE_DIR).parent / '.github' / 'scripts' / 'novedad_borrador.py'


def cargar():
    if not SCRIPT.exists():
        raise SkipTest('El script de la Action no está en este entorno')
    spec = importlib.util.spec_from_file_location('novedad_borrador', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DIFF_ENTRADA_NUEVA = """diff --git a/docs/team/changelog.md b/docs/team/changelog.md
--- a/docs/team/changelog.md
+++ b/docs/team/changelog.md
@@ -14,6 +14,10 @@
 ---
 
+## 2026-11-10 — FEAT-050: planilla de Medición en PDF (RF-03)
+
+En el detalle de cualquier presupuesto, el botón **Medición** abre la planilla.
+
 ## 2026-11-09 — FEAT-049: planilla de Colocación
"""

DIFF_ERRATA = """--- a/docs/team/changelog.md
+++ b/docs/team/changelog.md
@@ -20,1 +20,1 @@
-## 2026-11-09 — FEAT-049: planila de Colocación
+## 2026-11-09 — FEAT-049: planilla de Colocación
 
"""


class ScriptNovedadTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mod = cargar()

    def test_entrada_nueva_del_changelog(self):
        entradas = self.mod.entradas_changelog_nuevas(DIFF_ENTRADA_NUEVA)
        self.assertEqual(len(entradas), 1)
        titulo, cuerpo = entradas[0]
        self.assertEqual(titulo, 'Planilla de Medición en PDF (RF-03)')
        self.assertIn('botón **Medición**', cuerpo)
        self.assertNotIn('Colocación', cuerpo)

    def test_corregir_errata_no_es_entrada_nueva(self):
        self.assertEqual(self.mod.entradas_changelog_nuevas(DIFF_ERRATA), [])

    def test_numero_de_pr(self):
        commits = [{'asunto': 'Merge pull request #12 from x/y'}]
        self.assertEqual(self.mod.numero_pr(commits), 12)
        self.assertEqual(self.mod.numero_pr([{'asunto': 'feat: algo (#7)'}]), 7)
        self.assertIsNone(self.mod.numero_pr([{'asunto': 'asd'}]))

    def test_before_inutilizable(self):
        self.assertFalse(self.mod.before_utilizable('0' * 40))
        self.assertFalse(self.mod.before_utilizable(''))
        with mock.patch.object(self.mod.subprocess, 'run') as run:
            run.return_value.returncode = 128  # commit inexistente tras un force-push
            self.assertFalse(self.mod.before_utilizable('a' * 40))

    def test_sin_changelog_usa_el_commit(self):
        commits = [{'sha': 'f' * 40, 'autor': 'MKDIR', 'asunto': 'fix: algo', 'cuerpo': ''}]
        with mock.patch.object(self.mod, 'commits_del_push', return_value=commits), \
                mock.patch.object(self.mod, 'before_utilizable', return_value=False):
            p = self.mod.armar_payload('0' * 40, 'f' * 40)
        self.assertEqual(p['titulo'], 'fix: algo')
        self.assertEqual(p['texto_usuario'], '')
        self.assertIsNone(p['pr_numero'])
