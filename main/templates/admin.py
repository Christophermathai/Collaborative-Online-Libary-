class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['document', 'student', 'tnu_id', 'type', 'review', 'feedback_date']
        widgets = {
            'document': forms.Select(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Select Document',
                'id': 'Document',
                'required': True
            }),
            'student': forms.Select(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Select Student',
                'id': 'Student',
                'required': True
            }),
            'type': forms.NumberInput(attrs={
            'class': 'text-input w-input',
            'placeholder': 'Enter Type (e.g., 1 for MCQ, 2 for Flashcard)',
            'id': 'Type',
            'required': True,
            'readonly': True  
            }),
            'review': forms.Textarea(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Write your review here (optional)',
                'id': 'Review',
                'rows': 4
            }),
            'feedback_date': forms.DateTimeInput(attrs={
                'class': 'text-input w-input',
                'placeholder': 'Select Feedback Date and Time',
                'id': 'FeedbackDate',
                'type': 'datetime-local'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        tnu_id = cleaned_data.get("tnu_id")
        if tnu_id and tnu_id <= 0:
            self.add_error('tnu_id', "TNU ID must be a positive number.")
        return cleaned_data
    