from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [

    path('Home/',views.Home,name="Home"),
    path('Features/',views.Features),
    path('About/',views.About),
    path('Contact/',views.Contact),
    path('Sign In/', views.Signin,name='Signin'),
    path('Sign Up/',views.Signup,name="Signup") ,
    path('ASign Up/',views.afterSignup,name="afterSignup"),
    path('Login/',views.Login,name='Login'),
    path('Logout/',views.Logout,name='Logout'),
    path('DocumentADD',views.adddocpage,name="documentaddpage"),
    path('Search/',views.search,name="BookSearch"),
    path('Search_Result/',views.SearchResult,name="Search"),
    path('User Profile/',views.UserProfile,name="UserProfile"),
    path('Edit User/',views.Editusertemplate,name="edituview"),
    path('listdocument/',views.listdoc,name="listdocument"),
    path('pdfview/',views.pdf_view,name="Pdfview"),
    path('Summary/',views.summary,name="summary"),
    path('explain/',views.explain, name="explain"),
    path('lenghten/',views.lenght,name="lenght"),
    path('Shorten/',views.Shorten,name="Shorten"),
    path('Style/',views.Style,name="Style"),
    path('clan/',views.clan,name="clan"),
    path('Microphone/',views.Microphone,name="Microphone"),
    path('Flashcard/',views.flashcards,name="flashcard"),
    path('Mcq/',views.MCQ,name="Multiplechoicequestion"),
    path('Customize Flashcard/',views.CustomizeF,name="CustomF"),
    path("get-flash-styles/", views.get_flash_styles, name="get_flash_styles"),
    path("update-flash-style/", views.update_flash_style, name="update_flash_style"),
    path("Feedback/",views.FuserExperice, name="FEEDBACK"),
    path("Feedback/",views.MuserExperice, name="FEEDBACK2"),
    path("ReportDocument/",views.Report,name="Report")
]
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    