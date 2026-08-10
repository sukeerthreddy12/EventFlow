from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    # Normalize to: { "detail": "...", "errors": {...}? }
    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        response.data = {"detail": data["detail"]}
    elif isinstance(data, list):
        response.data = {"detail": data[0] if data else "Request failed.", "errors": data}
    elif isinstance(data, dict):
        detail = data.get("detail")
        if detail is None:
            # field errors → first message as detail
            first = next(iter(data.values()), "Request failed.")
            if isinstance(first, list) and first:
                detail = first[0]
            else:
                detail = str(first)
        response.data = {"detail": detail, "errors": data}
    return response