# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from .models import *
from django.db import models
from django.views.decorators.csrf import csrf_exempt 
import json

class CustomAdminSite(admin.AdminSite):
    site_header = 'GrowTogether Administration'
    site_title = 'GrowTogether Admin Panel'
    index_title = 'Welcome to GrowTogether Admin'
    index_template = 'admin/custom_index.html'

admin_site = CustomAdminSite(name='custom_admin')

class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'credits', 'join_date', 'is_active', 'flagged_documents','flash_style','sem')
    list_filter = ('is_active', 'join_date', 'flagged_documents','sem')
    search_fields = ('name', 'email','sem')
    ordering = ('-join_date',)
    class Media:
        css = {'all': ['css/admin_custom.css']}

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('Title', 'Author', 'Sem','Description', 'Discipline', 'UploadDate', 'Status','No_of_reports','P_key','view_pdf_button')
    list_filter = ('Status', 'Sem', 'Discipline')
    search_fields = ('Title', 'Author', 'Discipline')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:document_id>/view-pdf/', self.admin_site.admin_view(self.pdfview), name='view_pdf'),
        ]
        return custom_urls + urls

    @csrf_exempt
    def pdfview(self, request, document_id):
        document = tbl_document.objects.filter(pk=document_id).first()
        if not document:
            self.message_user(request, "Document not found", level="error")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))

        request.session['DocumentID'] = document.DocumentID
        path = document.FilePath[32:]
        pdf_url = path
        return render(request, "viewer.html", {"pdf_url": pdf_url})

    def view_pdf_button(self, obj):
        url = reverse('admin:view_pdf', kwargs={'document_id': obj.pk})
        return format_html(
            '<form method="post" action="{}">'
            '<input type="hidden" name="Title" value="{}" />'
            '<button type="submit" style="background-color: #007bff; color: white; border: none; padding: 5px 10px; cursor: pointer;">View PDF</button>'
            '</form>',
            url, obj.Title
        )
    view_pdf_button.short_description = 'View PDF'

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('UID', 'ActionType', 'ActionDate', 'Status')
    list_filter = ('Status', 'ActionType', 'ActionDate')
    search_fields = ('UID__name', 'ActionType')
    class Media:
        css = {'all': ['css/admin_custom.css']}

class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('flashcard_id', 'document', 'student', 'created_date')
    list_filter=('document','created_date')
    search_fields = ('document__Title', 'student__name')
    class Media:
        css = {'all': ['css/admin_custom.css']}

class McqAdmin(admin.ModelAdmin):
    list_display = ('mcq_id', 'document', 'student', 'created_date')
    list_filter=('document','created_date')
    search_fields = ('document__Title', 'student__name')
    class Media:
        css = {'all': ['css/admin_custom.css']}

class FlashCustomAdmin(admin.ModelAdmin):
    list_display = ('style_name', 'UID', 'background_color', 'text_color', 'font_choice')
    list_filter=('background_color','text_color','font_choice')
    search_fields = ('style_name', 'UID__name')
    class Media:
        css = {'all': ['css/admin_custom.css']}

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('feedback_id', 'document', 'student', 'type', 'review', 'feedback_date')
    list_filter = ('type', 'feedback_date')
    search_fields = ('review', 'type')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def document_report(self, obj):
        if obj.type == "Document Reported":
            return f"Document {obj.document} reported by {obj.student}"
        return None
    document_report.short_description = "Document Report"

admin_site.register(tbl_user, UserAdmin)
admin_site.register(tbl_document, DocumentAdmin)
admin_site.register(LogEntry, LogEntryAdmin)
admin_site.register(Flashcard, FlashcardAdmin)
admin_site.register(mcq, McqAdmin)
admin_site.register(tbl_flashcustom, FlashCustomAdmin)
admin_site.register(Feedback, FeedbackAdmin)

@admin_site.admin_view
@never_cache
def custom_admin_index(request):
    today = timezone.now().date()
    start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    total_users = tbl_user.objects.count()
    total_documents = tbl_document.objects.count()
    total_flashcards = Flashcard.objects.count()
    documents_today = tbl_document.objects.filter(UploadDate__range=(start_of_day, end_of_day)).count()
    flashcards_today = Flashcard.objects.filter(created_date__range=(start_of_day, end_of_day)).count()
    mcq_today = mcq.objects.filter(created_date__range=(start_of_day, end_of_day)).count()

    app_list = admin_site.get_app_list(request)
    model_counts = {
        'tbl_user': total_users,
        'tbl_document': total_documents,
        'LogEntry': LogEntry.objects.count(),
        'Flashcard': total_flashcards,
        'mcq': mcq.objects.count(),
        'tbl_flashcustom': tbl_flashcustom.objects.count(),
        'Feedback': Feedback.objects.count(),  # Added Feedback model count
    }

    for app in app_list:
        for model in app['models']:
            model_name = model['object_name']
            model['object_count'] = model_counts.get(model_name, 0)
            app_label = app['app_label']
            model_name_lower = model_name.lower()
            try:
                model['admin_url'] = reverse(f'admin:{app_label}_{model_name_lower}_changelist')
            except:
                model['admin_url'] = f"/admin/{app_label}/{model_name_lower}/"

    flashcard_data = Flashcard.objects.values('created_date').order_by('created_date')
    dates = [item['created_date'].strftime('%Y-%m-%d') for item in flashcard_data]
    count_by_date = {date: dates.count(date) for date in set(dates)}

    flashcard_dates = set(Flashcard.objects.values_list('created_date__date', flat=True))
    mcq_dates = set(mcq.objects.values_list('created_date__date', flat=True))
    all_dates = flashcard_dates.union(mcq_dates)
    date_list = sorted([d.strftime('%Y-%m-%d') for d in all_dates])
    date_data = {
        'labels': date_list,
        'flashcards': [Flashcard.objects.filter(created_date__date=date).count() for date in sorted(all_dates)],
        'mcqs': [mcq.objects.filter(created_date__date=date).count() for date in sorted(all_dates)],
    }

    action_types = LogEntry.objects.values('ActionType').annotate(count=models.Count('ActionType')).order_by('ActionType')
    action_data = {
        'labels': [item['ActionType'] for item in action_types],
        'counts': [item['count'] for item in action_types],
    }

    flashcard_counts = Flashcard.objects.values('document').annotate(count=models.Count('document'))
    mcq_counts = mcq.objects.values('document').annotate(count=models.Count('document'))
    logentry_counts = LogEntry.objects.values('DocumentID').annotate(count=models.Count('DocumentID'))

    document_usage = {}
    for entry in flashcard_counts:
        doc_id = entry['document']
        document_usage[doc_id] = document_usage.get(doc_id, 0) + entry['count']
    for entry in mcq_counts:
        doc_id = entry['document']
        document_usage[doc_id] = document_usage.get(doc_id, 0) + entry['count']
    for entry in logentry_counts:
        doc_id = entry['DocumentID']
        if doc_id:
            document_usage[doc_id] = document_usage.get(doc_id, 0) + entry['count']

    sorted_docs = sorted(document_usage.items(), key=lambda x: x[1], reverse=True)[:3]
    top_documents = []
    for doc_id, count in sorted_docs:
        doc = tbl_document.objects.get(DocumentID=doc_id)
        top_documents.append({
            'title': doc.Title,
            'author': doc.Author,
            'count': count
        })

    # Latest Reported Documents
    reported_feedback = Feedback.objects.filter(type="Document Reported").order_by('-feedback_date')[:3]
    latest_reported_documents = [
        {
            'title': feedback.document.Title,
            'student': feedback.student.name,
            'date': feedback.feedback_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        for feedback in reported_feedback
    ]

    user_records = [
        {'id': u.uid, 'name': u.name, 'email': u.email, 'date': u.join_date.strftime('%Y-%m-%d %H:%M:%S')}
        for u in tbl_user.objects.all()
    ]
    document_records = [
        {'id': d.DocumentID, 'title': d.Title, 'author': d.Author, 'date': d.UploadDate.strftime('%Y-%m-%d %H:%M:%S')}
        for d in tbl_document.objects.all()
    ]
    logentry_records = [
        {'id': l.LogID, 'uid': str(l.UID), 'action_type': l.ActionType, 'date': l.ActionDate.strftime('%Y-%m-%d %H:%M:%S')}
        for l in LogEntry.objects.all()
    ]
    flashcard_records = [
        {'id': f.flashcard_id, 'document_id': f.document.DocumentID, 'student': str(f.student), 'date': f.created_date.strftime('%Y-%m-%d %H:%M:%S')}
        for f in Flashcard.objects.all()
    ]
    mcq_records = [
        {'id': m.mcq_id, 'document_id': m.document.DocumentID, 'student': str(m.student), 'date': m.created_date.strftime('%Y-%m-%d %H:%M:%S')}
        for m in mcq.objects.all()
    ]
    flashcustom_records = [
        {'id': fc.id, 'style_name': fc.style_name, 'uid': str(fc.UID), 'date': timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        for fc in tbl_flashcustom.objects.all()
    ]
    customprofile_records = [
        {'id': cp.profile_id, 'user': str(cp.user), 'theme': cp.theme_preference, 'date': cp.last_updated.strftime('%Y-%m-%d %H:%M:%S')}
        for cp in CustomProfile.objects.all()
    ]
    feedback_records = [
        {'id': f.feedback_id, 'document': str(f.document), 'student': str(f.student), 'type': f.type, 'review': f.review or '', 'date': f.feedback_date.strftime('%Y-%m-%d %H:%M:%S')}
        for f in Feedback.objects.all()
    ]

    context = {
        'index_title': admin_site.index_title,
        'total_users': total_users,
        'total_documents': total_documents,
        'total_flashcards': total_flashcards,
        'documents_today': documents_today,
        'flashcards_today': flashcards_today,
        'MCQ_today': mcq_today,
        'app_list': app_list,
        'user': request.user,
        'model_counts': model_counts,
        'dates': json.dumps(list(set(dates))),
        'count_by_date': json.dumps(count_by_date),
        'date_data': json.dumps(date_data),
        'action_data': json.dumps(action_data),
        'today': today.strftime('%Y-%m-%d'),
        'top_documents': top_documents,
        'latest_reported_documents': latest_reported_documents,  # Added latest reported documents
        'user_records': json.dumps(user_records),
        'document_records': json.dumps(document_records),
        'logentry_records': json.dumps(logentry_records),
        'flashcard_records': json.dumps(flashcard_records),
        'mcq_records': json.dumps(mcq_records),
        'flashcustom_records': json.dumps(flashcustom_records),
        'customprofile_records': json.dumps(customprofile_records),
        'feedback_records': json.dumps(feedback_records),  # Added feedback records
    }
    return render(request, 'admin/custom_index.html', context)

admin_site.index = custom_admin_index