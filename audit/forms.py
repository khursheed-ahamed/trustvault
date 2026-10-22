from django import forms
from .models import AuditEvent


class AuditLogFilterForm(forms.Form):
    """Filter form for the administrative audit dashboard."""

    event_type = forms.ChoiceField(
        required=False,
        choices=[("", "-- All Event Types --")] + AuditEvent.EVENT_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[("", "-- All Outcomes --")] + AuditEvent.OUTCOME_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    actor = forms.CharField(
        required=False,
        label="Actor Username",
        widget=forms.TextInput(attrs={"placeholder": "Actor username...", "class": "form-control"}),
    )
    document_id = forms.IntegerField(
        required=False,
        label="Document ID",
        min_value=1,
        widget=forms.NumberInput(attrs={"placeholder": "Document ID...", "class": "form-control"}),
        error_messages={"invalid": "Document ID must be a valid positive number."},
    )
    start_date = forms.DateField(
        required=False,
        label="Start Date",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date", "placeholder": "YYYY-MM-DD", "class": "form-control"}),
        error_messages={"invalid": "Enter a valid start date in YYYY-MM-DD format."},
    )
    end_date = forms.DateField(
        required=False,
        label="End Date",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date", "placeholder": "YYYY-MM-DD", "class": "form-control"}),
        error_messages={"invalid": "Enter a valid end date in YYYY-MM-DD format."},
    )
