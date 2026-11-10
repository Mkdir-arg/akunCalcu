"""Arma el borrador de noticia de un push a main y lo manda a AkunCalcu (REQ-069).

Lo corre .github/workflows/novedades.yml. Variables de entorno:
  BEFORE, AFTER            rango del push (github.event.before / github.sha)
  NOVEDADES_URL            ej. https://<dominio>/novedades/api/borrador/
  NOVEDADES_BOT_SECRET     mismo valor que en Railway
  DRY_RUN=1                imprime el JSON y no envía nada

El texto para el equipo sale de las entradas nuevas de docs/team/changelog.md que trae el push
(el contenedor de producción no tiene docs/, por eso se extrae acá). Si no hay, queda el texto técnico.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

CHANGELOG = 'docs/team/changelog.md'
SIN_COMMIT = re.compile(r'^0+$')
PR_RE = re.compile(r'Merge pull request #(\d+)|\(#(\d+)\)\s*$')
FECHA_TITULO_RE = re.compile(r'^\[?\d{4}-\d{2}-\d{2}\]?\s*[—–-]\s*')
CODIGO_TITULO_RE = re.compile(r'^(FEAT|FIX|HFX)-\d+\s*[:—–-]\s*')


def git(*args):
    return subprocess.run(['git', *args], capture_output=True, text=True, encoding='utf-8', check=True).stdout


def before_utilizable(before):
    """False si es la primera subida (000…) o si el commit ya no existe (force-push)."""
    if not before or SIN_COMMIT.match(before):
        return False
    return subprocess.run(['git', 'cat-file', '-e', f'{before}^{{commit}}'], capture_output=True).returncode == 0


def commits_del_push(before, after):
    rango = [f'{before}..{after}'] if before_utilizable(before) else [after, '-1']
    salida = git('log', *rango, '--format=%H%x1f%an%x1f%s%x1f%b%x1e')
    commits = []
    for bloque in salida.split('\x1e'):
        partes = bloque.strip('\n').split('\x1f')
        if len(partes) == 4:
            commits.append({'sha': partes[0], 'autor': partes[1], 'asunto': partes[2], 'cuerpo': partes[3].strip()})
    return commits


def numero_pr(commits):
    for c in commits:
        m = PR_RE.search(c['asunto'])
        if m:
            return int(m.group(1) or m.group(2))
    return None


def entradas_changelog_nuevas(diff):
    """Devuelve [(titulo, cuerpo)] de los encabezados '## ' agregados al changelog en el diff."""
    entradas, actual = [], None
    previa = ''
    for cruda in diff.splitlines():
        if cruda.startswith('+++') or cruda.startswith('---'):
            continue
        if not cruda.startswith('+'):
            # Las líneas quitadas o de contexto cortan la entrada en curso.
            actual = None
            previa = cruda
            continue
        linea = cruda[1:]
        if linea.startswith('## ') and previa.startswith('-## '):
            # Reemplaza un encabezado viejo: es una corrección, no una entrada nueva.
            actual = None
        elif linea.startswith('## '):
            titulo = FECHA_TITULO_RE.sub('', linea[3:].strip())
            titulo = CODIGO_TITULO_RE.sub('', titulo)
            actual = [titulo[:1].upper() + titulo[1:], []]
            entradas.append(actual)
        elif actual is not None:
            actual[1].append(linea)
        previa = cruda
    return [(t, '\n'.join(c).strip()) for t, c in entradas if t]


def armar_payload(before, after):
    commits = commits_del_push(before, after)
    if not commits:
        return None
    diff = ''
    if before_utilizable(before):
        diff = git('diff', before, after, '--', CHANGELOG)
    entradas = entradas_changelog_nuevas(diff)

    no_merge = [c for c in commits if not c['asunto'].startswith('Merge ')] or commits
    if entradas:
        titulo = entradas[0][0]
        texto_usuario = entradas[0][1] if len(entradas) == 1 else '\n\n'.join(f'{t}\n{c}' for t, c in entradas)
    else:
        titulo = no_merge[0]['asunto']
        texto_usuario = ''

    tecnico = '\n'.join(f"- {c['sha'][:7]} {c['asunto']}" + (f"\n  {c['cuerpo'][:500]}" if c['cuerpo'] else '') for c in commits)
    return {
        'sha': after,
        'titulo': titulo[:200],
        'texto_usuario': texto_usuario,
        'texto_tecnico': tecnico[:8000],
        'pr_numero': numero_pr(commits),
        'autor': commits[0]['autor'][:100],
    }


def enviar(url, secreto, payload, intentos=3, espera=20):
    cuerpo = json.dumps(payload).encode('utf-8')
    for intento in range(1, intentos + 1):
        req = urllib.request.Request(url, data=cuerpo, method='POST', headers={
            'Content-Type': 'application/json', 'X-Bot-Secret': secreto, 'User-Agent': 'akuncalcu-novedades-action',
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f'OK {resp.status}: {resp.read().decode()}')
                return True
        except urllib.error.HTTPError as e:
            print(f'Intento {intento}: HTTP {e.code} {e.read().decode()[:300]}')
            if e.code in (400, 403):
                return False
        except urllib.error.URLError as e:
            print(f'Intento {intento}: {e.reason}')
        if intento < intentos:
            time.sleep(espera)
    return False


def main():
    payload = armar_payload(os.environ.get('BEFORE', ''), os.environ.get('AFTER') or git('rev-parse', 'HEAD').strip())
    if not payload:
        print('El push no trae commits nuevos: no hay borrador.')
        return 0
    if os.environ.get('DRY_RUN') == '1':
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    url, secreto = os.environ.get('NOVEDADES_URL', ''), os.environ.get('NOVEDADES_BOT_SECRET', '')
    if not url or not secreto:
        print('Faltan NOVEDADES_URL o NOVEDADES_BOT_SECRET en los secrets de GitHub: no se envía nada.')
        return 0
    return 0 if enviar(url, secreto, payload) else 1


if __name__ == '__main__':
    sys.exit(main())
