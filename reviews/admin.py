from django.contrib import admin
from .models import ProgrammingLanguage, ReviewTag, CodeReview, ReviewIssue, ReviewComment


@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'extension', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)
    search_fields = ('name', 'extension')


@admin.register(ReviewTag)
class ReviewTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class ReviewIssueInline(admin.TabularInline):
    """Ļauj rediģēt atrastās kļūdas tieši koda pārskata lapā"""
    model = ReviewIssue
    extra = 0
    fields = ('line_number', 'severity', 'tool', 'message', 'is_resolved')


class ReviewCommentInline(admin.StackedInline):
    """Ļauj pievienot komentārus koda pārskata iekšienē"""
    model = ReviewComment
    extra = 0


@admin.register(CodeReview)
class CodeReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'language', 'author', 'status', 'created_at')
    list_filter = ('status', 'language', 'created_at')
    search_fields = ('title', 'source_code')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ReviewIssueInline, ReviewCommentInline]


@admin.register(ReviewIssue)
class ReviewIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'line_number', 'severity', 'tool', 'is_resolved')
    list_filter = ('severity', 'tool', 'is_resolved')
    search_fields = ('message', 'suggestion')


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'review', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content',)