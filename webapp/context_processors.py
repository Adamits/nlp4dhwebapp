def current_active(request):
    """
    Put an "active" key in the context
    so that the navbar knows which page
    is currently active.
    """
    pagename = request.path
    active = ""
    if pagename == "/corpora":
        active = "home"
    elif pagename == "/corpora/concordance":
        active = "concordance"
    elif pagename == "/corpora/analysis":
        active = "analysis"

    return {"active": active}
