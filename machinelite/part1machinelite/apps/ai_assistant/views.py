from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .services import AIAssistantEngine

@login_required
def chat_view(request):
    """Render full AI Assistant Interface."""
    return render(request, 'ai_assistant/chat.html')

@csrf_exempt
@login_required
def ask_api(request):
    """AJAX API endpoint for AI Business Assistant."""
    if request.method == 'POST':
        query = request.POST.get('query', '')
        if not query:
            return JsonResponse({'error': 'Query string required'}, status=400)
        
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return JsonResponse({'error': 'No organization tenant context'}, status=400)

        engine = AIAssistantEngine(tenant)
        result = engine.ask(query)
        return JsonResponse(result)
    return JsonResponse({'error': 'POST method required'}, status=405)
