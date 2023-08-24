from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import openai

openai.api_key='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'

# Create your views here.
def chatPage(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login-user")
    context = {}
    return render(request, "chat/chatPage.html", context)

def chatZoom(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login-user")
    context = {"mode":"chat"}
    return render(request, "chat/chatZoom.html", context)

def interviewZoom(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login-user")
    context = {"mode":"interview"}
    return render(request, "chat/chatInterview.html", context)

@csrf_exempt
def chatgpt(r):
    openai.organization = 'org-J4KgUhEy9jQlMW0RyMERkiN9'
    openai.api_key='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'
    if r.method == 'GET':
        messages = json.loads(r.GET['messages'])
    else:
        messages = json.loads(r.body)
    print(messages)
    completion=openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages['messages']
    )   
    reply = completion.choices[0].message.content
    return JsonResponse({'code':0,'reply':reply})
