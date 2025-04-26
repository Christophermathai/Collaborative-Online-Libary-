from django.shortcuts import render, redirect
from .forms import TblUserForm, AdddocumentForm, flashStyleForm
from .models import tbl_user, tbl_document, LogEntry, tbl_flashcustom, Flashcard, mcq, Feedback
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login as django_login, logout, get_user
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from django.contrib.auth.decorators import login_required  # Added for login restriction
from django.views.decorators.csrf import csrf_protect  # Added for explicit CSRF protection
from django.views.decorators.cache import never_cache
####Plagarisum
from django.core.files.storage import FileSystemStorage
from docx import Document
from django.core.files.uploadedfile import InMemoryUploadedFile
import string
import hashlib
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
from django.views.decorators.csrf import csrf_exempt

api_key ="add your api key here"

# Create your views here.
def Home(request):
    return render(request, 'Home.html')

def Features(request):
    return render(request, 'features.html')

def About(request):
    return render(request, 'aboutpage.html')

def Contact(request):
    return render(request, 'Contact.html')

def Signin(request):
    return render(request, 'Sign_in.html')

def Signup(request):
    form = TblUserForm()
    return render(request, 'Sign_up.html', {'form': form})

@csrf_protect  # Explicit CSRF protection
def afterSignup(request):
    form = TblUserForm()
    if request.method == 'POST':
        if 'submit' in request.POST:
            form = TblUserForm(request.POST)  # Bind the form with POST data
            if form.is_valid():  # Validate the form
                user = form.save(commit=False)  # Don't save to the database yet
                user.password = make_password(form.cleaned_data['password'])  # Hash the password
                send_account_creation_email(user.email, user.name)
                user.save()  # Save the user instance to the database
                return render(request, 'Sign_in.html')
            else:
                # If the form is invalid, re-render the sign-up page with the form errors
                return render(request, 'Sign_up.html', {'form': form})
    else:
        form = TblUserForm()
    return render(request, 'Sign_up.html', {'form': form})

def send_account_creation_email(user_email, user_name):
    try:
        # Render the email template
        context = {'user_name': user_name}
        html_message = render_to_string('account_creation_email.html', context)

        # Create and send the email
        email = EmailMessage(
            subject="Welcome to Our Service",
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],  # Fixed typo: SearchResultto -> to
        )
        email.content_subtype = "html"
        email.send()

        return True

    except Exception:
        return False
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect



@csrf_exempt
def Login(request):
    form = TblUserForm()
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("Cookies:", request.COOKIES)
        csrf_post = request.POST.get('csrfmiddlewaretoken')
        csrf_cookie = request.COOKIES.get('csrftoken')
        print(f"CSRF from POST: {csrf_post}")
        print(f"CSRF from Cookie: {csrf_cookie}")
        if csrf_post != csrf_cookie:
            print("CSRF mismatch detected!")
        data = request.POST
        username = data.get("Email-address")
        password = data.get("Password")
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            django_login(request, user)
            print(request.session.items())
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
            return render(request, "User_Page.html", {'top_documents': top_documents})
        else:
            # Redirect instead of render on failure
            return redirect('Signin')  # Assumes Signin redirects to Login or serves Sign_in.html
    response = render(request, "Sign_in.html", {'form': form})
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def Logout(request):
    logout(request)
    return redirect('Home')

from pdf2image import convert_from_bytes, convert_from_path
import pytesseract
from PIL import Image
import docx
import pdfkit

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def adddocpage(request):
    form = AdddocumentForm()
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        file_extension = filename.split('.')[-1].lower()
        if file_extension == 'docx' or file_extension == 'doc':
            Result = convert_docx_to_pdf(uploaded_file, filename)
            pdf_filename = filename.replace(".docx", ".pdf")
            pdf_path = os.path.join(settings.MEDIA_ROOT, "Temp", pdf_filename)
            if Result == 1:
                images = convert_from_path(pdf_path)
                paragraphs = ""
                for i, page in enumerate(images):
                    paragraphs += pytesseract.image_to_string(page, lang="eng")
                pre_text = preprocess_text(paragraphs)
                generated_hash = generate_plagiarism_key(pre_text)
                hash_result = comparehash(generated_hash)
                if hash_result == 0:
                    file_path = os.path.join(settings.MEDIA_ROOT, 'Pdf', pdf_filename)
                    instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
                    os.rename(pdf_path, file_path)
                    form = AdddocumentForm(request.POST)
                    if form.is_valid():
                        user = form.save(commit=False)
                        user.FilePath = file_path
                        user.P_key = generated_hash
                        user.UID_id = request.session.get('_auth_user_id')
                        user.Course_ID = 101
                        user.save()
                        instance.credits = instance.credits + 15
                        instance.save()
                        message = "success"
                    else:
                        message = "failed"
            context = {'form': form, 'message': message}
            return render(request, 'add_document.html', context)
        elif file_extension == 'pdf':
            poppler_path = "C:\\Program Files\\poppler-24.08.0\\Library\\bin"
            pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            text = ""
            temp = uploaded_file
            uploaded_filed = uploaded_file.read()
            pages = convert_from_bytes(uploaded_filed, dpi=400)
            paragraphs = ""
            for i, page in enumerate(pages):
                paragraphs += pytesseract.image_to_string(page, lang="eng")
            pre_text = preprocess_text(paragraphs)
            generated_hash = generate_plagiarism_key(pre_text)
            hash_result = comparehash(generated_hash)
            print(pre_text)
            if hash_result == 0:
                file_path = os.path.join(settings.MEDIA_ROOT, 'Pdf', temp.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                form = AdddocumentForm(request.POST)
                instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
                if form.is_valid():
                    user = form.save(commit=False)
                    user.FilePath = file_path
                    user.P_key = generated_hash
                    user.UID_id = request.session.get('_auth_user_id')
                    user.Course_ID = 101
                    user.save()
                    instance.credits = instance.credits + 15
                    instance.save()
                    message = "success"
            else:
                message = "failed"
            context = {'form': form, 'message': message}
            return render(request, 'add_document.html', context)
        else:
            fmessage = "The books are not correct file Type<br>Valid file types are Docx and pdf"
            context = {'form': form, 'fmessage': fmessage}
            print(fmessage)
            return render(request, 'add_document.html', context)
    return render(request, 'add_document.html', {'form': form})

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect 
def listdoc(request):
    UID = request.session.get('_auth_user_id')
    documents = tbl_document.objects.filter(UID=UID)
    session_data = tbl_user.objects.get(pk=UID)
    context = {
                    'documents': documents,
                    'session_data': session_data,
                }
    return render(request,"userdocument.html",context)
    

from docx2pdf import convert

def convert_docx_to_pdf(uploaded_file, docx_filename):
    docx_path = os.path.join(settings.MEDIA_ROOT, 'Document', docx_filename)
    pdf_filename = docx_filename.replace(".docx", ".pdf").replace(".doc", ".pdf")
    pdf_path = os.path.join(settings.MEDIA_ROOT, "Temp", pdf_filename)
    with open(docx_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    try:
        convert(docx_path, os.path.dirname(pdf_path))
        if os.path.exists(pdf_path):
            return 1
        else:
            print("⚠ Conversion failed: PDF file not found.")
            return 0
    except Exception as e:
        print(f"🚨 Error converting DOCX to PDF: {e}")
        return 0

def preprocess_text(content):
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(content.lower())
    filtered_tokens = [word for word in tokens if word not in stop_words and word not in string.punctuation]
    return " ".join(filtered_tokens)

def generate_plagiarism_key(content):
    processed_content = preprocess_text(content)
    return hashlib.sha256(processed_content.encode()).hexdigest()

def comparehash(new_hash):
    stored_hashes = tbl_document.objects.values_list('P_key', flat=True)
    if new_hash in stored_hashes:
        print(f"Match found: {new_hash}")
        return 1
    else:
        print(f"No match found for: {new_hash}")
        return 0

from django.db.models import Q

@csrf_protect  # Explicit CSRF protection
def SearchResult(request):
    if request.method == 'POST':
        data = request.POST
        csrf_post = request.POST.get('csrfmiddlewaretoken')
        csrf_cookie = request.COOKIES.get('csrftoken')
        print(f"CSRF from POST: {csrf_post}")
        print(f"CSRF from Cookie: {csrf_cookie}")
        S = data.get("Search")
        Result = tbl_document.objects.filter(Q(Title__icontains=S) | Q(Author__icontains=S) | Q(Description__icontains=S))
        return render(request, 'Result.html', {'Result': Result, 'View': True})


def search (request):
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
    return render(request, "User_Page.html", {'top_documents': top_documents})
    
@login_required(login_url='Signin')  # Restrict access to logged-in users
def UserProfile(request):
    UID = request.session.get('_auth_user_id')
    session_data = tbl_user.objects.get(pk=UID)
    no_of_documents = tbl_document.objects.filter(UID=UID).count()
    documents = tbl_document.objects.filter(UID=UID)
    context = {
        'session_data': session_data,
        'no_of_documents': no_of_documents,
        'documents': documents,
    }
    return render(request, 'Profile.html', context)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def Editusertemplate(request):
    UID = request.session.get('_auth_user_id')
    session_data = tbl_user.objects.get(pk=UID)
    Userform = TblUserForm(instance=session_data, hide_field=['name'])
    if request.method == "POST":
        form = TblUserForm(request.POST, instance=session_data)
        data = request.POST
        sem = data.get("sem")
        if form.is_valid():
            sem_value = Userform['sem'].value()
            if int(sem) < int(sem_value):
                message = "Can't Downgrade the Sem"
                context = {
                    'session_data': session_data,
                    'message': message,
                    'form': Userform,
                }
                return render(request, 'EditUser.html', context)
            else:
                form.save()
                no_of_documents = tbl_document.objects.filter(UID=UID).count()
                documents = tbl_document.objects.filter(UID=UID)
                session_data = tbl_user.objects.get(pk=UID)
                context = {
                    'session_data': session_data,
                    'no_of_documents': no_of_documents,
                    'documents': documents,
                }
                return render(request, 'Profile.html', context)
        else:
            message = "User input not valid"
            print(form.errors)
            context = {
                'session_data': session_data,
                'message': message,
                'form': Userform,
            }
            return render(request, 'EditUser.html', context)
    context = {
        'session_data': session_data,
        'form': Userform,
    }
    return render(request, 'EditUser.html', context)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def pdf_view(request):
    instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
    if instance.credits >= 3:
        if request.method == 'POST':
            rtitle = request.POST.get('Title')
            documents = tbl_document.objects.filter(Title=rtitle).first()
            request.session['DocumentID'] = documents.DocumentID
            print(documents)
            path = documents.FilePath
            path = path[32:]
            pdf_url = path
            return render(request, "viewer.html", {"pdf_url": pdf_url})
        file_path = os.path.join(settings.MEDIA_ROOT, 'pdf', "default.pdf")
        file_path = file_path[32:]
        print(file_path)
        return render(request, "viewer.html", {"pdf_url": file_path})
    else:
        form = AdddocumentForm()
        context = {
            'message': "Expired",
            'form': form,
        }
        return render(request, 'add_document.html', context)

# AI tools
import json
import google.generativeai as genai

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST (ensure this is intentional)
def summary(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    action = "Summary"
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        lang_prompt = f"Find the language associated with the given text. As the answer, provide only the language name. The text = {notes}"
        response = model.generate_content(lang_prompt)
        Language = response.text.strip() if response.text else "Unknown"
        summary_prompt = f"Summarize the text to make it easier for learning: {notes}"
        response = model.generate_content(summary_prompt)
        summary_text = response.text.strip() if response.text else ""
        status = 1 if summary_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=summary_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": summary_text})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def explain(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    action = "Explanation"
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        lang_prompt = f"Find the language associated with the given text. Provide only the language name. The text = {notes}"
        response = model.generate_content(lang_prompt)
        Language = response.text.strip() if response.text else "Unknown"
        explanation_prompt = f"Explain the following text in simple words for better understanding: {notes}"
        response = model.generate_content(explanation_prompt)
        explanation_text = response.text.strip() if response.text else ""
        status = 1 if explanation_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=explanation_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": explanation_text})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def lenght(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    action = "Lenghten"
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        lang_prompt = f"Find the language associated with the given text. As the answer, provide only the language name. The text = {notes}"
        response = model.generate_content(lang_prompt)
        Language = response.text.strip() if response.text else "Unknown"
        text = "lenght the text as it makes it twice it original word add more emotion and care to it text is  ", notes
        response = model.generate_content(text)
        summary_text = response.text.strip() if response.text else ""
        status = 1 if summary_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=summary_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": response.text})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def Shorten(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    action = "Shorten"
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        lang_prompt = f"Find the language associated with the given text. Provide only the language name. The text = {notes}"
        response = model.generate_content(lang_prompt)
        Language = response.text.strip() if response.text else "Unknown"
        shorten_prompt = f"Make the following text significantly shorter while keeping the key message intact: {notes}"
        response = model.generate_content(shorten_prompt)
        shortened_text = response.text.strip() if response.text else ""
        status = 1 if shortened_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=shortened_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": shortened_text})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def Style(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        style_format = data.get('elemtdata', "")
        action = "Style Adjustment:" + style_format
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        lang_prompt = f"Find the language associated with the given text. Provide only the language name. The text = {notes}"
        response = model.generate_content(lang_prompt)
        Language = response.text.strip() if response.text else "Unknown"
        style_prompt = f"Rewrite the following text in a {style_format} style while maintaining its meaning: {notes}"
        response = model.generate_content(style_prompt)
        styled_text = response.text.strip() if response.text else ""
        status = 1 if styled_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=styled_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": styled_text})
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def clan(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        style_format = data.get('elemtdata', "")
        action = "Translation:" + style_format
        Language = style_format
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Translate the following text into {style_format}. Use simpler words while maintaining the meaning: {notes}"
        response = model.generate_content(prompt)
        styled_text = response.text.strip() if response.text else ""
        status = 1 if styled_text else 0
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText=notes,
            OutputText=styled_text,
            Language=Language,
            Status=status
        )
        return JsonResponse({"message": styled_text})
    return JsonResponse({"error": "Invalid request"}, status=400)

import speech_recognition as sr
import pyttsx3
import logging

r = sr.Recognizer()
engine = pyttsx3.init()
logger = logging.getLogger(__name__)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def Microphone(request):
    user_id = request.session.get('_auth_user_id')
    document_id = request.session.get('DocumentID')
    if not user_id:
        return JsonResponse({"error": "User not authenticated"}, status=401)
    try:
        user = tbl_user.objects.get(pk=user_id)
    except tbl_user.DoesNotExist:
        logger.error(f"User with ID {user_id} not found.")
        return JsonResponse({"error": "User not found"}, status=404)
    document_instance = None
    if document_id:
        try:
            document_instance = tbl_document.objects.get(pk=document_id)
        except tbl_document.DoesNotExist:
            logger.warning(f"Document with ID {document_id} not found.")
            document_instance = None
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    try:
        genai.configure(api_key=Api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    action = "Microphone"
    language = "en-US"
    try:
        with microphone as source:
            logger.info("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logger.info("Listening for speech input...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=30)
            logger.info("Recognizing audio...")
            text = recognizer.recognize_google(audio, language=language).lower()
            LogEntry.objects.create(
                UID=user,
                DocumentID=document_instance,
                ActionType=action,
                InputText="None",
                OutputText=text,
                Language=language,
                Status=1
            )
            logger.info(f"Speech recognized successfully: {text}")
            return JsonResponse({"message": text})
    except sr.WaitTimeoutError:
        logger.warning("Speech recognition timed out.")
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText="None",
            OutputText="",
            Language=language,
            Status=0
        )
        return JsonResponse({"error": "No speech detected within timeout"}, status=408)
    except sr.UnknownValueError:
        logger.warning("Could not understand the audio.")
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText="None",
            OutputText="",
            Language=language,
            Status=0
        )
        return JsonResponse({"error": "Could not understand the audio"}, status=400)
    except sr.RequestError as e:
        logger.error(f"Speech recognition request failed: {str(e)}")
        LogEntry.objects.create(
            UID=user,
            DocumentID=document_instance,
            ActionType=action,
            InputText="None",
            OutputText="",
            Language=language,
            Status=0
        )
        return JsonResponse({"error": f"Speech service error: {str(e)}"}, status=503)
    except Exception as e:
        logger.error(f"Unexpected error in speech recognition: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def flashcards(request):
    print("hello")
    if request.method == "POST":
        user_id = request.session.get('_auth_user_id')
        rtitle = request.POST.get('Title')
        instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
        if instance.credits >= 3:
            documents = tbl_document.objects.filter(Title=rtitle).first()
            if not documents:
                return render(request, "Flashcards.html", {"error": "Document not found"}, status=404)
            request.session['DocumentID'] = documents.DocumentID
            request.session['dtitle'] = rtitle
            FilePath = documents.FilePath
            FilePath = FilePath[43:]
            FilePath = os.path.join(settings.MEDIA_ROOT, 'pdf', FilePath)
            if not os.path.exists(FilePath):
                return render(request, "Flashcards.html", {"error": "File not found"}, status=404)
            try:
                pages = convert_from_path(FilePath)
                paragraphs = ""
                for page in pages:
                    paragraphs += pytesseract.image_to_string(page, lang="eng")
                genai.configure(api_key=Api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                text = "Summarize the text and generate 10 flashcards. Retrieve only the flash card questions and output only the questions  them as a normal string separated by ';'.", "text=", paragraphs
                response = model.generate_content(text)
                text = response.text
                q = text
                answer = "Generate the answer for these question from text provided with the query and output only the answer  them as a normal string separated by ';'.the question are :", response.text, " and the is text=", paragraphs
                answer = model.generate_content(answer)
                answer = answer.text
                a = answer
                text = json.dumps(text.split(';'))
                answer = json.dumps(answer.split(';'))
                print(text)
                instance.credits = instance.credits - 3
                instance.save()
                card_style=tbl_flashcustom.objects.get(pk=instance.flash_style)
                print("/n/n/n/n",card_style)
                Flashcard.objects.create(
                    student=instance,
                    document=documents,
                    flashcard_Questions=q,
                    flashcard_Answers=a,
                )
                return render(request, "Flashcards.html", {"content": text, "answer": answer,"cardcolor":card_style.background_color,"textcolor":card_style.text_color,"font":card_style.font_choice})
            except Exception as e:
                print(f"Error: {e}")
                return render(request, "Flashcards.html", {"error": str(e)}, status=500)
        else:
            form = AdddocumentForm()
            context = {
                'message': "Expired",
                'form': form,
            }
            return render(request, 'add_document.html', context)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def CustomizeF(request):
    form = flashStyleForm()
    if request.method == 'POST':
        form = flashStyleForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.UID_id = request.session.get('_auth_user_id')
            user.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    context = {
        'form': form
    }
    return render(request, "customflashcards.html", context)

@login_required(login_url='Signin')  # Restrict access to logged-in users
def get_flash_styles(request):
    styles = list(tbl_flashcustom.objects.filter(UID=request.session.get('_auth_user_id')).values("id", "style_name"))
    return JsonResponse({"styles": styles})

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def update_flash_style(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_style = data.get("flash_style")
            user = request.user
            user.flash_style = new_style
            user.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def MCQ(request):
    if request.method == "POST":
        user_id = request.session.get('_auth_user_id')
        rtitle = request.POST.get('Title')
        instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
        if instance.credits >= 3:
            documents = tbl_document.objects.filter(Title=rtitle).first()
            if not documents:
                return render(request, "mcq.html", {"error": "Document not found"}, status=404)
            request.session['DocumentID'] = documents.DocumentID
            request.session['dtitle'] = rtitle
            FilePath = documents.FilePath
            FilePath = FilePath[43:]
            FilePath = os.path.join(settings.MEDIA_ROOT, 'pdf', FilePath)
            if not os.path.exists(FilePath):
                return render(request, "mcq.html", {"error": "File not found"}, status=404)
            try:
                pages = convert_from_path(FilePath)
                paragraphs = ""
                for page in pages:
                    paragraphs += pytesseract.image_to_string(page, lang="eng")
                genai.configure(api_key=Api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                text = "Summarize the text and generate 10 Multiple choice question. Retrieve only the Multiple choice questions and output only the questions  them as a normal string separated by ';'.", "text=", paragraphs
                response = model.generate_content(text)
                text = response.text
                q = text
                answer = "Generate the answer for these question from text provided with the query and output only the answer  them as a normal string separated by ';'.the question are :", response.text, " and the is text=", paragraphs
                answer = model.generate_content(answer)
                answer = answer.text
                a = answer
                text = json.dumps(text.split(';'))
                answer = json.dumps(answer.split(';'))
                instance.credits = instance.credits - 3
                instance.save()
                mcq.objects.create(
                    student=instance,
                    document=documents,
                    MCQ_questions=q,
                    MCQ_answers=a,
                )
                print(text)
                return render(request, "mcq.html", {"content": text, "answer": answer})
            except Exception as e:
                print(f"Error: {e}")
                return render(request, "mcq.html", {"error": str(e)}, status=500)
        else:
            form = AdddocumentForm()
            context = {
                'message': "Expired",
                'form': form,
            }
            return render(request, 'add_document.html', context)

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def FuserExperice(request):
    if request.method == "POST":
        instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
        doc_id = request.session.get('dtitle')
        documents = tbl_document.objects.filter(Title=doc_id).first()
        data = request.POST
        Review = data.get("review")
        print(doc_id)
        Feedback.objects.create(
            student=instance,
            document=documents,
            type='FlashCard',
            review=Review
        )
        return render(request, "User_Page.html", {'msg': 'Thank you for your submission'})
    return render(request, "feedback.html", {'type': 'FlashCard'})

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_protect  # Explicit CSRF protection
def MuserExperice(request):
    if request.method == "POST":
        instance = tbl_user.objects.get(pk=request.session.get('_auth_user_id'))
        doc_id = request.session.get('dtitle')
        documents = tbl_document.objects.filter(Title=doc_id).first()
        data = request.POST
        Review = data.get("review")
        print(doc_id)
        Feedback.objects.create(
            student=instance,
            document=documents,
            type='MCQ',
            review=Review
        )
        return render(request, "User_Page.html", {'msg': 'Thank you for your submission'})
    return render(request, "feedback.html", {'type': 'MCQ'})

@login_required(login_url='Signin')  # Restrict access to logged-in users
@csrf_exempt  # Exempt CSRF for JSON POST
def Report(request):
    user_id = request.session.get('_auth_user_id')
    DocumentID = request.session.get('DocumentID')
    if request.method == "POST":
        data = json.loads(request.body)
        notes = data.get('notes', "")
        try:
            user = tbl_user.objects.get(pk=user_id)
        except tbl_user.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=400)
        try:
            document_instance = tbl_document.objects.get(pk=DocumentID) if DocumentID else None
        except tbl_document.DoesNotExist:
            document_instance = None
        print(notes)
        Feedback.objects.create(
            student=user,
            document=document_instance,
            type='Docuemnt Reported',
            review=notes,
        )
        document_instance.No_of_reports = document_instance.No_of_reports + 1
        document_instance.save()
        return JsonResponse({"message": 'Docuemnt Reported'})
    return JsonResponse({"error": "Invalid request"}, status=400)
