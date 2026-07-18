from .models import Ticket


def issue_ticket(registration) -> Ticket:
    """Create a CONFIRMED ticket if registration is CONFIRMED. Idempotent."""
    if registration.status != registration.Status.CONFIRMED:
        raise ValueError("Tickets are only issued for CONFIRMED registrations.")

    ticket, _created = Ticket.objects.get_or_create(
        registration=registration,
        defaults={"status": Ticket.Status.CONFIRMED},
    )
    return ticket


def cancel_ticket(registration) -> None:
    """Mark linked ticket CANCELLED if it exists and is not already USED."""
    ticket = getattr(registration, "ticket", None)
    if ticket is None:
        try:
            ticket = Ticket.objects.get(registration=registration)
        except Ticket.DoesNotExist:
            return

    if ticket.status == Ticket.Status.USED:
        return  # already checked in — leave as USED

    if ticket.status != Ticket.Status.CANCELLED:
        ticket.status = Ticket.Status.CANCELLED
        ticket.save(update_fields=["status", "updated_at"])