import re
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Q


from apps.forms import TicketForm, ReviewForm, UsersForm
from apps.models import Ticket, Review, UserFollows
from apps.post import get_all_posts
# Create your views here.


def index(request):

    if request.user.is_authenticated:
        return render(request, 'apps/index.html')
    else:
        return redirect(reverse('apps:login'))


@login_required
def flux(request):

    context = {}

    RForm = ReviewForm(request.POST or None)
    posts_list = get_all_posts('all')

    context['posts'] = posts_list
    context['RForm'] = RForm

    return render(request, 'apps/flux.html', context)


@login_required
def posts(request):

    context = {}

    RForm = ReviewForm(request.POST or None)
    posts_list = get_all_posts(user=request.user)
    context['posts'] = posts_list
    context['RForm'] = RForm

    return render(request, 'apps/posts.html', context)


@login_required
def subscription(request):

    context = {}

    if request.method == "POST":
        UForm = UsersForm(request.POST or None)
        if UForm.is_valid():
            username = UForm.cleaned_data['username']
            user = User.objects.filter(username=username).first()
            if user:
                userFollows = UserFollows()
                userFollows.user = request.user
                userFollows.followed_user = user
                userFollows.save()
            else:
                error_message = "Username inconnu."
                messages.error(request, error_message)
        errors = UForm.errors or None

    UForm = UsersForm()
    following_users = UserFollows.objects.filter(user=request.user)
    followed_users = UserFollows.objects.filter(followed_user=request.user)

    context['UForm'] = UForm
    context['following_users'] = following_users
    context['followed_users'] = followed_users

    return render(request, 'apps/subscription.html', context)


@login_required
def unsubscription(request):

    if request.method == "POST":
        followed_user_id = request.POST.get('followed_user_id')
        followed_user = get_object_or_404(User, pk=followed_user_id)
        if followed_user:
            UserFollows.objects.filter(
                user=request.user, followed_user=followed_user).delete()

    return redirect(reverse('apps:subscription'))


@login_required
def create_ticket(request):

    context = {}
    context['title'] = 'Créer un ticket'

    TForm = TicketForm(request.POST or None)
    if request.method == "POST":
        if TForm.is_valid():
            ticket = TForm.save(commit=False)
            ticket.user = request.user
            ticket.save()

    context['TForm'] = TForm

    return redirect(reverse('apps:flux'))


@login_required
def update_ticket(request, id):

    context = {}
    context['title'] = 'Modifier un ticket'
    ticket = get_object_or_404(Ticket, pk=id)
    context['ticket'] = ticket

    if request.method == "POST":
        TForm = TicketForm(request.POST, instance=ticket)
        TForm.save()

        return redirect(reverse('apps:posts'))

    else:
        TForm = TicketForm(instance=ticket)

    context['TForm'] = TForm

    return render(request, 'apps/ticket.html', context)


@ login_required
def add_review(request):

    context = {}
    context['title'] = 'Ajouter une critique'

    RForm = ReviewForm(request.POST or None)
    if request.method == "POST":
        if RForm.is_valid():
            ticket_id = request.POST.get('post_id')
            ticket = get_object_or_404(Ticket, pk=ticket_id)
            review = RForm.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()

        return redirect(reverse('apps:flux'))

    context['RForm'] = RForm

    return render(request, 'apps/review.html', context)


@ login_required
def update_review(request, id):

    context = {}
    context['title'] = 'Modifier une critique'
    review = get_object_or_404(Review, pk=id)
    context['review'] = review
    context['ticket'] = review.ticket

    if request.method == "POST":
        RForm = ReviewForm(request.POST, instance=review)
        RForm.save()

        return redirect(reverse('apps:posts'))
    else:
        RForm = ReviewForm(instance=review)

    context['RForm'] = RForm

    return render(request, 'apps/review.html', context)


@ login_required
def create_review(request):

    context = {}
    context['title'] = 'Créer une critique'

    if request.GET.get('review_id'):
        review = get_object_or_404(Review, pk=request.GET.get('review_id'))
        ticket = get_object_or_404(Ticket, pk=request.GET.get('ticket_id'))
        review_initial = {
            'rating': review.rating,
            'headline': review.headline,
            'body': review.body,
        }
        context['ticket'] = ticket
    else:
        review_initial = {}

    TForm = TicketForm(request.POST or None)
    RForm = ReviewForm(request.POST or None, initial=review_initial)
    if request.method == "POST":
        if TForm.is_valid() and RForm.is_valid():
            ticket = TForm.save(commit=False)
            ticket.user = request.user
            ticket.save()
            review = RForm.save(commit=False)
            review.ticket = ticket
            review.user = request.user
            review.save()
        return redirect(reverse('apps:flux'))

    context['TForm'] = TForm
    context['RForm'] = RForm

    return render(request, 'apps/review.html', context)


def connexion(request):

    context = {}
    AForm = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST":
        if AForm.is_valid():
            username = AForm.cleaned_data['username']
            password = AForm.cleaned_data['password']
            user = authenticate(
                request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse('apps:index'))
            else:
                error_message = "Identifiant ou mot de passe incorrect."
                messages.error(request, error_message)
        context['AForm'] = AForm
    else:
        AForm = AuthenticationForm(request)
        context['AForm'] = AForm

    return render(request, 'apps/login.html', context)


def deconnexion(request):

    logout(request)

    return redirect(reverse('apps:index'))


def signup(request):

    UForm = UserCreationForm(request.POST or None)
    if request.method == "POST":
        if UForm.is_valid():
            user = UForm.save()
            group = Group.objects.get(name='Community')
            group.user_set.add(user)
            return redirect(reverse('apps:login'))
        else:
            error_message = "Identifiant ou mot de passe incorrect."
            messages.error(request, error_message)

    context = {'UForm': UForm}

    return render(request, 'apps/signup.html', context)
