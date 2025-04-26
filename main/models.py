from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class tbl_user(AbstractBaseUser):
    uid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, null=False)
    email = models.EmailField(max_length=40, unique=True, null=False)
    password = models.CharField(max_length=128, null=False)
    credits = models.IntegerField(default=0)
    join_date = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)
    sem = models.IntegerField(null=True, blank=True)
    course = models.CharField(max_length=40, null=True, blank=True)
    flagged_documents = models.IntegerField(default=0)
    flash_style = models.IntegerField(
        null=True, blank=True,
        default=None,
        verbose_name="Flash card styling",
        db_column="Flash_style"
    )
    type = models.IntegerField(default=2)
    last_login = models.DateTimeField(null=True, blank=True)  # Add last_login field
    is_staff = models.BooleanField(default=False)
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'tbl_user'
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = 'main'

    def __str__(self):
        return f"{self.name} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    def has_perm(self, perm, obj=None):
        """Check if the user has a specific permission."""
        return True

    # This method is required for admin access
    def has_module_perms(self, app_label):
        """Check if the user has permissions for a specific app."""
        return True
    
from django.db import models
from django.utils.timezone import now

class tbl_document(models.Model):
    DocumentID = models.AutoField(primary_key=True)  # Unique identifier for each document
    UID = models.ForeignKey('main.tbl_user', on_delete=models.CASCADE)  # Foreign key to tbl_Student
    Title = models.CharField(max_length=100, null=False)  # Title of the document
    Author = models.CharField(max_length=30, null=False)  # Name of the author
    Description = models.TextField(null=True, blank=True)  # Brief description of the document
    Course_ID = models.CharField(max_length=30, null=True)
    Sem = models.IntegerField(null=False)  # Semester to which the book is related
    FilePath = models.CharField(max_length=255, null=False)  # Path to the uploaded file
    UploadDate = models.DateTimeField(default=now)  # Date and time the document was uploaded
    Status = models.BooleanField(default=True)  # Indicates active (True) or inactive (False)
    Discipline = models.CharField(max_length=50, null=False)  # Academic discipline or subject area
    No_of_reports = models.IntegerField(default=0)  # No. of times the document/book has been reported
    P_key = models.TextField(null=False,default="none")

    def __str__(self):
        return f"{self.Title} by {self.Author}"
    class Meta:
        app_label = 'main'
    
class LogEntry(models.Model):
    LogID = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    UID = models.ForeignKey(tbl_user, on_delete=models.CASCADE)  # User performing the action
    DocumentID = models.ForeignKey(tbl_document, null=True, blank=True, on_delete=models.SET_NULL)  # Optional document reference
    ActionType = models.CharField(max_length=20)  # Type of action performed
    InputText = models.TextField()  # Original text before transformation
    OutputText = models.TextField()  # Transformed text after action
    Language = models.CharField(max_length=20, null=True, blank=True)  # Optional language field
    ActionDate = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp
    Status = models.BooleanField(default=True)  # 1 for success, 0 for failure

    def __str__(self):
        return f"{self.UID} - {self.ActionType} on {self.ActionDate.strftime('%Y-%m-%d %H:%M:%S')}"
    class Meta:
        app_label = 'main'


class tbl_flashcustom(models.Model):
    # Field to store the style name
    style_name = models.CharField(
        max_length=100,
        verbose_name="Style Name"
    )
    UID = models.ForeignKey('main.tbl_user', on_delete=models.CASCADE, default=1 )  # Foreign key to tbl_Student
    # Field to store the background color
    background_color = models.CharField(
        max_length=7,  # e.g., '#ff0000'
        verbose_name="Background Color"
    )

    # Field to store the text color
    text_color = models.CharField(
        max_length=7,  # e.g., '#ff0000'
        verbose_name="Text Color"
    )

    # Field to store the font choice
    font_choice = models.CharField(
        max_length=50,
        choices=[
            ('Arial', 'Arial'),
            ('Verdana', 'Verdana'),
            ('Tahoma', 'Tahoma'),
            ('Trebuchet MS', 'Trebuchet MS'),
            ('Georgia', 'Georgia'),
            ('Times New Roman', 'Times New Roman'),
            ('Courier New', 'Courier New'),
            ('Lucida Console', 'Lucida Console')
        ],
        verbose_name="Font Choice"
    )

    def __str__(self):
        return self.style_name
    class Meta:
        app_label = 'main'



class Flashcard(models.Model):
    flashcard_id = models.AutoField(primary_key=True)  # Unique identifier for each flashcard set
    document = models.ForeignKey('tbl_document', on_delete=models.CASCADE, db_column='DocumentID')  # References tbl_Document
    student = models.ForeignKey('main.tbl_user', on_delete=models.CASCADE, db_column='uid')  # References tbl_User
    flashcard_Questions = models.TextField()  # Generated flashcard content separated with ";"
    flashcard_Answers = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)  # Timestamp of when the flashcards were created

    class Meta:
        db_table = 'tbl_flashcard'  # Table name in the database
        app_label = 'main'

    def __str__(self):
        return f"Flashcard {self.flashcard_id}"
    


class mcq(models.Model):
    mcq_id = models.AutoField(primary_key=True)  # Unique identifier for each MCQ set
    document = models.ForeignKey('tbl_document', on_delete=models.CASCADE, db_column='DocumentID')  # Links to tbl_Document
    student = models.ForeignKey('main.tbl_user', on_delete=models.CASCADE, db_column='uid')  # Identifies the student who generated the MCQs
    MCQ_questions = models.TextField()  # Stores all questions, separated by ";"
    MCQ_answers = models.TextField()  # Stores correct answers, separated by ";"
    created_date = models.DateTimeField(auto_now_add=True, db_column='CreatedDate')  # Timestamp of when the MCQs were generated

    class Meta:
        db_table = 'tbl_mcq'  # Maps to the tbl_mcq table in the database
        app_label = 'main'

    def __str__(self):
        return f"MCQ {self.mcq_id} for Document {self.document_id}"
    
    
    
class CustomProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        'main.tbl_user',
        on_delete=models.CASCADE,
        related_name='custom_profile'
    )
    
    # Profile customization fields
    avatar_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        default='https://example.com/default-avatar.png'
    )
    
    bio = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Short biography or description"
    )
    
    theme_preference = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Light Theme'),
            ('dark', 'Dark Theme'),
            ('custom', 'Custom Theme')
        ],
        default='dark'
    )
    
    accent_color = models.CharField(
        max_length=7,
        default='#ffc44d',
        help_text="User's preferred accent color in hex"
    )
    
    banner_image = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        default=None
    )
    
    display_stats = models.BooleanField(
        default=True,
        help_text="Show profile statistics publicly"
    )
    
    last_updated = models.DateTimeField(
        default=now,
        help_text="Last profile update timestamp"
    )
    
    social_links = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Social media links stored as JSON"
    )
    
    class Meta:
        db_table = 'tbl_custom_profile'
        verbose_name = "Custom Profile"
        verbose_name_plural = "Custom Profiles"
        app_label = 'main'
    
    def __str__(self):
        return f"{self.user.name}'s Profile"
    
    def get_profile_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.avatar_url != 'https://example.com/default-avatar.png',
            self.bio is not None,
            self.banner_image is not None,
            bool(self.social_links)
        ]
        completed = sum(1 for field in fields if field)
        return (completed / len(fields)) * 100
    
class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    document = models.ForeignKey('tbl_document', on_delete=models.CASCADE, db_column='DocumentID')  # Links to tbl_Document
    student = models.ForeignKey('main.tbl_user', on_delete=models.CASCADE, db_column='uid')  # Identifies the student who generated the MCQs
    type = models.CharField(
        max_length=500,
        null=True,)  # Differentiates between Flash Card and MCQ
    review = models.TextField(blank=True, null=True)  # Optional
    feedback_date = models.DateTimeField(default=now) 