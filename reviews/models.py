from django.db import models
from django.contrib.auth.models import User


class ProgrammingLanguage(models.Model):
    """1. tabula: Atbalstītās programmēšanas valodas"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Valodas nosaukums")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Identifikators (slug)")
    extension = models.CharField(max_length=10, verbose_name="Faila paplašinājums (piem., .py)")
    is_active = models.BooleanField(default=True, verbose_name="Aktīvs")

    class Meta:
        verbose_name = "Programmēšanas valoda"
        verbose_name_plural = "Programmēšanas valodas"
        ordering = ['name']

    def __str__(self):
        return self.name


class ReviewTag(models.Model):
    """2. tabula: Problēmu kategorijas / birkas (Security, Performance utt.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Birkas nosaukums")
    description = models.TextField(blank=True, verbose_name="Apraksts")

    class Meta:
        verbose_name = "Problēmas birka"
        verbose_name_plural = "Problēmu birkas"

    def __str__(self):
        return self.name


class CodeReview(models.Model):
    """3. tabula: Galvenais koda pārskats (ieraksts par analīzi)"""
    STATUS_CHOICES = [
        ('pending', 'Gaida rindā / Tiek apstrādāts'),
        ('completed', 'Pabeigts'),
        ('failed', 'Kļūda analīzē'),
    ]

    title = models.CharField(max_length=255, verbose_name="Nosaukums / Uzdevums")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Autors", null=True, blank=True)
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.PROTECT, related_name='reviews', verbose_name="Valoda")
    source_code = models.TextField(verbose_name="Pirmkods pārbaudei")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statuss")
    summary = models.TextField(blank=True, verbose_name="AI kopsavilkums par kodu")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Izveides datums")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Pēdējo izmaiņu datums")

    class Meta:
        verbose_name = "Koda pārskats"
        verbose_name_plural = "Koda pārskati"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.language.name}) - {self.created_at.strftime('%d.%m.%Y %H:%M')}"


class ReviewIssue(models.Model):
    """4. tabula: Katra konkrētā atrastā kļūda vai ieteikums kodā"""
    SEVERITY_CHOICES = [
        ('error', 'Kritiska kļūda (Error)'),
        ('warning', 'Brīdinājums (Warning)'),
        ('info', 'Ieteikums (Info)'),
    ]

    TOOL_CHOICES = [
        ('linter', 'Statiskais skeneris (Linter)'),
        ('ai', 'Mākslīgais intelekts (AI Agent)'),
    ]

    review = models.ForeignKey(CodeReview, on_delete=models.CASCADE, related_name='issues', verbose_name="Saistītais pārskats")
    line_number = models.PositiveIntegerField(verbose_name="Rindas numurs", null=True, blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning', verbose_name="Svarīgums")
    tool = models.CharField(max_length=20, choices=TOOL_CHOICES, default='ai', verbose_name="Atrada rīks")
    message = models.TextField(verbose_name="Kļūdas apraksts")
    suggestion = models.TextField(blank=True, verbose_name="Ieteikums labojumam")
    is_resolved = models.BooleanField(default=False, verbose_name="Atrisināts / Ignorēts")
    
    tags = models.ManyToManyField(ReviewTag, blank=True, related_name='issues', verbose_name="Birkas")

    class Meta:
        verbose_name = "Atrastā problēma"
        verbose_name_plural = "Atrastās problēmas"
        ordering = ['line_number']

    def __str__(self):
        return f"Rinda {self.line_number or 'N/A'}: [{self.severity.upper()}] {self.message[:40]}"


class ReviewComment(models.Model):
    """5. tabula: Lietotāju/recenzentu komentāri pie pārskata"""
    review = models.ForeignKey(CodeReview, on_delete=models.CASCADE, related_name='comments', verbose_name="Pārskats")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Komentāra autors")
    content = models.TextField(verbose_name="Komentāra saturs")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Pievienošanas datums")

    class Meta:
        verbose_name = "Recenzijas komentārs"
        verbose_name_plural = "Recenzijas komentāri"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} komentārs pie #{self.review.id}"