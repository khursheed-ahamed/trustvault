import os
from django import forms
from django.contrib.auth import get_user_model
from .models import Document, DocumentPermission

ALLOWED_EXTENSIONS = [".pdf", ".txt", ".docx"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file", "category"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Document title"}),
            "category": forms.TextInput(attrs={"placeholder": "e.g. Legal, Finance, HR (optional)"}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if not uploaded_file:
            raise forms.ValidationError("A document file is required.")

        # Validate maximum file size (10 MB)
        if uploaded_file.size > MAX_FILE_SIZE:
            size_mb = uploaded_file.size / (1024 * 1024)
            raise forms.ValidationError(
                f"File size exceeds the 10 MB limit ({size_mb:.2f} MB uploaded)."
            )

        # Validate allowed extensions
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(ALLOWED_EXTENSIONS)
            raise forms.ValidationError(
                f"Invalid file extension '{ext}'. Only {allowed_list} files are allowed."
            )

        return uploaded_file


class DocumentPermissionForm(forms.ModelForm):
    class Meta:
        model = DocumentPermission
        fields = ["user", "permission"]

    def __init__(self, *args, document=None, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        qs = User.objects.all()

        # Exclude document owner
        if document and document.owner_id:
            qs = qs.exclude(pk=document.owner_id)

        # Exclude current logged-in owner
        if current_user and current_user.pk:
            qs = qs.exclude(pk=current_user.pk)

        self.fields["user"].queryset = qs.order_by("username")
        self.fields["user"].empty_label = "Choose a user..."
