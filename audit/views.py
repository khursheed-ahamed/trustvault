from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from .forms import AuditLogFilterForm
from .models import AuditEvent


@login_required
def admin_audit_dashboard(request):
    """
    Administrator-only audit activity dashboard.
    Strictly restricted to users with role == 'ADMIN'.
    Note: is_staff or is_superuser alone does NOT grant access to this view.
    """
    if getattr(request.user, "role", None) != "ADMIN":
        raise PermissionDenied("Access restricted to users with the 'ADMIN' role.")

    events = AuditEvent.objects.select_related("actor", "document").order_by("-created_at")

    form = AuditLogFilterForm(request.GET or None)
    if form.is_valid():
        event_type = form.cleaned_data.get("event_type")
        outcome = form.cleaned_data.get("outcome")
        actor = form.cleaned_data.get("actor")
        document_id = form.cleaned_data.get("document_id")
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")

        if event_type:
            events = events.filter(event_type=event_type)
        if outcome:
            events = events.filter(outcome=outcome)
        if actor:
            events = events.filter(actor__username__icontains=actor)
        if document_id:
            events = events.filter(document_id=document_id)
        if start_date:
            events = events.filter(created_at__date__gte=start_date)
        if end_date:
            events = events.filter(created_at__date__lte=end_date)
    elif request.GET:
        # Invalid filter inputs should not trigger server errors or bypass filtering
        events = events.none()

    return render(
        request,
        "audit/admin_audit_dashboard.html",
        {
            "events": events,
            "filter_form": form,
        },
    )
