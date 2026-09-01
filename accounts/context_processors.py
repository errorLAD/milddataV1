def guest_status(request):
    """
    Expose guest status details to all templates for Guest Mode banner rendering.
    """
    if not hasattr(request, "session"):
        return {"is_guest": False}

    is_guest = request.session.get("is_guest", False)
    guest_id = request.session.get("guest_id", None)
    
    return {
        "is_guest": is_guest,
        "guest_id": guest_id,
    }
