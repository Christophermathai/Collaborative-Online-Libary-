from django import forms
from .models import tbl_user,tbl_document,tbl_flashcustom,Feedback

class TblUserForm(forms.ModelForm):
    confirm_password = forms.CharField(
        max_length=256,
        widget=forms.PasswordInput(attrs={
            'class': 'text-input w-input',
            'placeholder': 'Confirm password',
            'id': 'Password',
            'required': True
        }),
        label='Confirm Password'
    )

    class Meta:
        model = tbl_user
        fields = ['name', 'email', 'password', 'sem', 'course']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'text-input w-input readonlyedit',
                'placeholder': 'Your Name',
                'id': 'Name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Your email',
                'id': 'Email-address-2',
                'required': True
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Your password',
                'id': 'Password-2',
                'required': True
            }),
            'sem': forms.TextInput(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Your Sem',
                'id': 'Sem',
                'required': True
            }),
            'course': forms.TextInput(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Your Course',
                'id': 'Course',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        hide_field = kwargs.pop('hide_field', None)  # Capture the field to hide
        super().__init__(*args, **kwargs)

        # Apply 'readonly' attribute only to specified fields
        if isinstance(hide_field, list):  # Ensure it's a list
            for field in hide_field:
                if field in self.fields:
                    self.fields[field].widget = forms.HiddenInput()
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        email = self.cleaned_data['email']
        if tbl_user.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data

class AdddocumentForm(forms.ModelForm):
    class Meta:
        model = tbl_document  # Reference the actual model
        fields = ('Author', 'Title', 'Discipline', 'Sem', 'Description')  # Use tuple/list for fields
        Discipline_CHOICES = [
        ('Literature', 'Literature'),
        ('Physics', 'Physics'),
        ('Maths', 'Maths'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('Statatics', 'Statatics'),
        ('Sports', 'Sports'),
        ('Computer Science', 'Computer Science'),
        ('Architecture', 'Architecture'),
        ('Law','Law'),
        ('Economics', 'Economics'),
        ('History', 'History'),
        ('Geography', 'Geography'),
        ('Comerce', 'Comerce')
    ]
        widgets = {
            'Author': forms.TextInput(attrs={
                'class': "text-input w-input",
                'maxlength': 30,
                'placeholder': "Your Document's author",
                'id': "Author-2",
                'required': True
            }),
            'Title': forms.TextInput(attrs={
                'class': "text-input w-input",
                'maxlength': "100",
                'placeholder': "Your Document Title",
                'id': "Title",
                "required": True,
            }),
            'Discipline': forms.Select(choices=Discipline_CHOICES, attrs={
                'class': "select-field w-select",
                'id': "Discipline",
                'required': True,
            }),
            'Sem': forms.TextInput(attrs={
                'class': "text-input w-input",
                'maxlength': 1,
                'placeholder': "Your Sem",
                'id': "Sem",
                'required': True,
            }),
            'Description': forms.Textarea(attrs={
                'class': "textarea w-input",
                'placeholder': "Book Description",
                'maxlength': 5000,
                'id': "Description",
                'style': "width: 768px; height: 236px;",
            }),
        }
        

class flashStyleForm(forms.ModelForm):
    # Style Name field
    class Meta:
        model = tbl_flashcustom
        fields = ['style_name', 'background_color', 'text_color', 'font_choice']
    style_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'text-input w-input',
                'placeholder': 'Enter Style Name:',
                'style': 'color:var(--accent);'
            }
        ),
        label="Style Name"
    )
    
    # Background Color Picker
    background_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type': 'color',
                'id': 'html5colorpicker',
                'onchange': 'clickColor(0, -1, -1, 5)',
                'value': '#ff0000',
                'class': 'text-input w-input'
            }
        ),
        label="Pick a Background Color"
    )

    # Text Color Picker
    text_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'type': 'color',
                'id': 'html5colorpicker',
                'onchange': 'clickColor(0, -1, -1, 5)',
                'value': '#ff0000',
                'class': 'text-input w-input'
            }
        ),
        label="Pick a Text Color"
    )

    # Font Selection Dropdown
    font_choice = forms.ChoiceField(
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
        widget=forms.Select(
            attrs={
                'class': 'text-input w-input',
                'style': 'padding: 5px; font-family: Arial; border-radius: 5px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); color:white;'
            }
        ),
        label="Choose a Font"
    )
