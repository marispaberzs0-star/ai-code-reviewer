# reviews/services.py
import json
import subprocess
import tempfile
import os
import sys
import shutil
from pathlib import Path
from django.conf import settings
from google import genai
from google.genai import types
from .models import ReviewIssue


def get_cppcheck_path():
    """Atrod portatīvo vai sistēmas Cppcheck"""
    local_portable = Path(settings.BASE_DIR) / "bin" / "cppcheck" / "cppcheck.exe"
    if local_portable.exists():
        return str(local_portable)
    standard_path = Path("C:/Program Files/Cppcheck/cppcheck.exe")
    if standard_path.exists():
        return str(standard_path)
    return shutil.which("cppcheck")


def run_ai_review(review, linter_findings=""):
    """
    Izsauc Google Gemini AI koda analīzei ar automātisku fallback sarakstu.
    Ja viena modeļa serveri ir noslogoti (503), automātiski pieslēdz nākamo modeli.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("KĻŪDA: GEMINI_API_KEY nav atrasts sistēmā!")
        return

    # Pieejamo modeļu prioritāšu saraksts (ja kāds ir aizņemts, ņem nākamo)
    models_to_try = [
        'gemini-3.5-flash-lite',
        'gemini-3.1-flash-lite',
        'gemini-3.8-flash',
    ]

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Tu esi Senior koda recenzents un programmatūras arhitekts.
    Tavs uzdevums ir veikt koda pārskatu (Code Review) šim {review.language.name} kodam.

    KODS PĀRBAUDEI:
    ```{review.language.slug}
    {review.source_code}
    ```

    STATISKO SKENERU (LINTERU) ATRADUMI KONSOLĒ:
    {linter_findings if linter_findings else "Statiskie skeneri kļūdas neatrada vai šai valodai nav pieejami."}

    TAVI UZDEVUMI:
    1. Ņem vērā konsoles atradumus, bet NEDUBLĒ tieši tās pašas sintakses kļūdas, ja vien nav nepieciešams sniegt padziļinātu skaidrojumu.
    2. Analizē biznesa loģiku, bezgalīgos ciklus, ievades validāciju (input validation) un arhitektūru.
    3. Uzraksti kodolīgu kopsavilkumu par kodu latviešu valodā.

    ATBILDI TIKAI UN VIENĪGI DERĪGĀ JSON FORMĀTĀ bez papildu markdown formatējuma ap to:
    {{
        "summary": "Kvalitatīvs kopsavilkums par koda kvalitāti, arhitektūru un riskiem latviešu valodā (2-4 teikumi).",
        "issues": [
            {{
                "line_number": 15,
                "severity": "warning",
                "message": "Kļūdas apraksts latviešu valodā",
                "suggestion": "Ieteikums labojumam latviešu valodā"
            }}
        ]
    }}
    Piezīme: 'severity' drīkst būt tikai 'error', 'warning' vai 'info'.
    """

    for model_name in models_to_try:
        try:
            print(f"Mēģinām palaist modeli: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            if response.text:
                data = json.loads(response.text)

                if "summary" in data and data["summary"]:
                    review.summary = data["summary"]
                    review.save()

                for item in data.get("issues", []):
                    ReviewIssue.objects.create(
                        review=review,
                        line_number=item.get("line_number"),
                        severity=item.get("severity", "warning"),
                        tool="ai",
                        message=item.get("message", ""),
                        suggestion=item.get("suggestion", "")
                    )

                print(f"AI analīze veiksmīgi pabeigta ar modeli {model_name}!")
                return  # Veiksmīgi beidzam darbu

        except Exception as e:
            print(f"Modelis {model_name} nebija pieejams ({e}), mēģinām rezerves modeli...")
            continue

    print("KĻŪDA: Neviens no AI modeļiem pašlaik nav pieejams.")


def run_static_analysis(review):
    """
    Galvenais apstrādes cauruļvads (Pipeline):
    1. Izpilda konsoles skenerus un fiksē atradumus
    2. Nodot kodu + atradumus AI aģentam
    """
    suffix = review.language.extension or '.txt'
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as temp_file:
        temp_file.write(review.source_code)
        temp_path = temp_file.name

    linter_log = []

    try:
        # === 1. KONSOLĒS SKENERI (Python caur sys.executable - apejam Windows Security blokus) ===
        if review.language.slug == 'python':
            # Ruff
            try:
                ruff_res = subprocess.run(
                    [sys.executable, '-m', 'ruff', 'check', temp_path, '--output-format=json'],
                    capture_output=True, text=True
                )
                if ruff_res.stdout:
                    for item in json.loads(ruff_res.stdout):
                        msg = f"Rinda {item.get('location', {}).get('row', 1)}: [{item.get('code')}] {item.get('message')}"
                        linter_log.append(f"[Ruff]: {msg}")
                        ReviewIssue.objects.create(
                            review=review,
                            line_number=item.get('location', {}).get('row', 1),
                            severity='warning',
                            tool='linter',
                            message=f"[{item.get('code')}] {item.get('message')}",
                            suggestion=item.get('fix', {}).get('message', '') if item.get('fix') else ''
                        )
            except Exception as e:
                print(f"Ruff kļūda: {e}")

            # Bandit (laižam caur Python interpreteru, lai Windows nebloķētu .exe)
            try:
                bandit_res = subprocess.run(
                    [sys.executable, '-m', 'bandit', '-f', 'json', temp_path],
                    capture_output=True, text=True
                )
                if bandit_res.stdout:
                    for item in json.loads(bandit_res.stdout).get('results', []):
                        msg = f"Rinda {item.get('line_number', 1)}: [Bīstamība {item.get('issue_severity')}] {item.get('issue_text')}"
                        linter_log.append(f"[Bandit]: {msg}")
                        sev = {'HIGH': 'error', 'MEDIUM': 'warning', 'LOW': 'info'}.get(item.get('issue_severity'), 'warning')
                        ReviewIssue.objects.create(
                            review=review,
                            line_number=item.get('line_number', 1),
                            severity=sev,
                            tool='linter',
                            message=f"[Drošība / {item.get('test_id')}]: {item.get('issue_text')}",
                            suggestion=f"Līnija: {item.get('code', '').strip()}"
                        )
            except Exception as e:
                print(f"Bandit kļūda: {e}")

        # === 2. KONSOLĒS SKENERIS (C++) ===
        elif review.language.slug == 'cpp':
            cppcheck_bin = get_cppcheck_path()
            if cppcheck_bin:
                try:
                    cpp_res = subprocess.run(
                        [
                            cppcheck_bin,
                            '--enable=warning,style,performance,portability',
                            '--suppress=missingIncludeSystem',
                            '--template={line}:::{severity}:::{message}',
                            temp_path
                        ],
                        capture_output=True, text=True
                    )
                    output = cpp_res.stderr or cpp_res.stdout
                    if output:
                        for line in output.splitlines():
                            if ':::' in line:
                                parts = line.split(':::')
                                if len(parts) >= 3:
                                    line_str, severity_raw, msg = parts[0], parts[1], parts[2]
                                    if 'Active checkers' in msg:
                                        continue
                                    line_no = int(line_str) if line_str.isdigit() else 1
                                    linter_log.append(f"[Cppcheck {severity_raw}] Rinda {line_no}: {msg}")
                                    sev = 'error' if severity_raw == 'error' else ('warning' if severity_raw in ['warning', 'style', 'performance'] else 'info')
                                    ReviewIssue.objects.create(
                                        review=review,
                                        line_number=line_no,
                                        severity=sev,
                                        tool='linter',
                                        message=f"[Cppcheck / {severity_raw}]: {msg}",
                                        suggestion="Ieteicams optimizēt kodu un pārbaudīt atmiņas lietojumu."
                                    )
                except Exception as e:
                    print(f"Cppcheck kļūda: {e}")

        # === 3. AI RECENZĒŠANA ===
        run_ai_review(review, linter_findings="\n".join(linter_log))

        review.status = 'completed'
        review.save()

    except Exception as e:
        print(f"Pipeline kļūda: {e}")
        review.status = 'failed'
        review.save()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)