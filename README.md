Tīmekļa lietojumprogramma koda automātiskai pārbaudei. Sistēma pārbauda kodu ar konsoles linteriem (Ruff, Bandit, Cppcheck) un Google Gemini mākslīgo intelektu, atrodot kļūdas un sniedzot ieteikumus latviešu valodā.

## Tehnoloģijas
- Python 3.11 / Django 5
- SQLite datubāze
- Google Gemini API (`google-genai`)
- Ruff, Bandit, Cppcheck
- Tailwind CSS

---

## Uzstādīšanas un palaišanas soļi

1. Solis: Virtuālās vides izveide un aktivizēšana
Izmantojot Conda:

conda create -n ai_reviewer python=3.11 -y
conda activate ai_reviewer

Vai izmantojot standarta venv:

python -m venv venv
venv\Scripts\activate

3. Solis: Projekta atkarību instalēšana

Instalējiet visas nepieciešamās bibliotēkas:

pip install -r requirements.txt

4. Solis: API atslēgas pievienošana (.env)

Projekta saknes mapē izveidojiet failu .env un ievadiet savu bezmaksas Google Gemini API atslēgu:

GEMINI_API_KEY=jūsu_api_atslēga_šeit
(Atslēgu var iegūt bez maksas vietnē https://aistudio.google.com/apikey)

5. Solis: Datubāzes sagatavošana
Izveidojiet datubāzes tabulas:

python manage.py migrate

6. Solis: Programmēšanas valodu ielāde
Pievienojiet sistēmā atbalstītās valodas:

python manage.py shell -c "from reviews.models import ProgrammingLanguage; langs = [('Python', 'python', '.py'), ('C++', 'cpp', '.cpp'), ('C#', 'csharp', '.cs'), ('JavaScript', 'javascript', '.js'), ('HTML', 'html', '.html'), ('Java', 'java', '.java'), ('PHP', 'php', '.php'), ('SQL', 'sql', '.sql')]; [ProgrammingLanguage.objects.get_or_create(slug=s, defaults={'name': n, 'extension': e}) for n, s, e in langs]"

7. Solis: Administratora (CMS) izveide
Izveidojiet piekļuves kontu administratora panelim:

python manage.py createsuperuser

8. Solis: Servera palaišana
Palaidiet izstrādes serveri:


python manage.py runserver

Piekļuve sistēmai
Galvenā lapa: http://127.0.0.1:8000/
Pārskatu saraksts: http://127.0.0.1:8000/reviews/
CMS administratora panelis: http://127.0.0.1:8000/admin/