# reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import CodeReview, ProgrammingLanguage
from .services import run_static_analysis


def home(request):
    """Galvenā vizītkarte"""
    languages = ProgrammingLanguage.objects.filter(is_active=True)
    return render(request, 'home.html', {'languages': languages})


def register(request):
    """Lietotāja reģistrācija"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Apsveicam, {user.username}! Jūsu konts ir izveidots. Pārbaudes tagad ir neierobežotas!")
            return redirect('review_list')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def review_list(request):
    """
    CRUD: Read (Konfidencialitāte: rāda TIKAI savus pārskatus!)
    """
    if request.user.is_authenticated:
        # Reģistrēts lietotājs redz TIKAI savus kodus (vai administrators redz visus)
        if request.user.is_staff:
            reviews = CodeReview.objects.all()
        else:
            reviews = CodeReview.objects.filter(author=request.user)
    else:
        # Viesis redz TIKAI tos kodus, kurus pats izveidojis šajā pārlūka sesijā
        guest_ids = request.session.get('guest_review_ids', [])
        reviews = CodeReview.objects.filter(id__in=guest_ids)

    return render(request, 'reviews/review_list.html', {'reviews': reviews})

def review_create(request):
    """CRUD: Create (ar stingru, nesadegošu 10 pārbaužu limitu)"""
    GUEST_LIMIT = 10

    # 1. Nolasām stingro nesadegošo skaitītāju
    guest_spent = request.session.get('guest_review_count', 0) if not request.user.is_authenticated else 0

    # 2. Ja limits izsmelts un mēģina iesniegt kodu (POST)
    if not request.user.is_authenticated and guest_spent >= GUEST_LIMIT:
        messages.error(
            request,
            f"⚠️ Jūsu bezmaksas viesu limits ({GUEST_LIMIT} pārbaudes) ir pilnībā iztērēts! "
            "Pārbaužu dzēšana neatjauno bezmaksas kvotu. Lūdzu, reģistrējieties bezlimita piekļuvei."
        )
        return redirect('register')

    if request.method == 'POST':
        title = request.POST.get('title')
        language_id = request.POST.get('language')
        source_code = request.POST.get('source_code')

        language = get_object_or_404(ProgrammingLanguage, id=language_id)

        review = CodeReview.objects.create(
            title=title,
            language=language,
            source_code=source_code,
            status='pending',
            author=request.user if request.user.is_authenticated else None
        )

        if not request.user.is_authenticated:
            # Pievienojam ID ekrāna sarakstam
            guest_ids = request.session.get('guest_review_ids', [])
            guest_ids.append(review.id)
            request.session['guest_review_ids'] = guest_ids

            # PALIKTINĀM NESADEGOŠO SKAITĪTĀJU (tas nekad nesamazinās!)
            request.session['guest_review_count'] = guest_spent + 1
            request.session.modified = True

        run_static_analysis(review)
        return redirect('review_detail', pk=review.id)

    # Vizuālais atlikums ekrānam
    remaining_checks = None
    if not request.user.is_authenticated:
        remaining_checks = max(0, GUEST_LIMIT - guest_spent)

    languages = ProgrammingLanguage.objects.filter(is_active=True)
    return render(request, 'reviews/review_create.html', {
        'languages': languages,
        'remaining_checks': remaining_checks,
        'guest_limit': GUEST_LIMIT
    })


def review_delete(request, pk):
    review = get_object_or_404(CodeReview, pk=pk)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            guest_ids = request.session.get('guest_review_ids', [])
            if review.id in guest_ids:
                guest_ids.remove(review.id)
                request.session['guest_review_ids'] = guest_ids
                request.session.modified = True
                # UZMANĪBU: guest_review_count MĒS NEAIZTIKAM! Patērētā pārbaude netiek atgriezta!

        review.delete()
        messages.success(request, "Pārskats veiksmīgi izdzēsts.")
        return redirect('review_list')

    return redirect('review_detail', pk=pk)


def review_detail(request, pk):
    review = get_object_or_404(CodeReview, pk=pk)

    # Aizsardzība: neļaujam skatīties svešu kodu
    if not request.user.is_staff:
        if review.author and review.author != request.user:
            messages.error(request, "Jums nav piekļuves tiesību šim pārskatam!")
            return redirect('review_list')
        elif not review.author and review.id not in request.session.get('guest_review_ids', []):
            messages.error(request, "Jums nav piekļuves tiesību šim pārskatam!")
            return redirect('review_list')

    return render(request, 'reviews/review_detail.html', {'review': review})


