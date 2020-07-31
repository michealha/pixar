from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from accounts.tokens import account_activation_token
from accounts.forms import SignUpForm, StoryForm, ImageForm, ProfilePhotoForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.models import User 
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone 
from social_django.models import UserSocialAuth
from accounts.models import Follow, Story, Like, Comment, Image 
from django.db.models import Sum, Count
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.conf import settings 
from django.forms import modelformset_factory
import requests
try:
    from django.utils import simplejson as json
except ImportError:
    import json
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import loader 


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = "Activate Simple Messages Account"
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def account_activation_sent(request):
    return render(request, 'account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'account_activation_invalid.html')


@login_required
def social_settings(request):
    user = request.user 

    try:
        facebook_login = user.social_auth.get(provider='facebook')
    except UserSocialAuth.DoesNotExist :
        facebook_login = None 
    
    can_disconnect = (user.social_auth.count() > 1 or user.has_usable_password())
    return render(request, 'social_settings.html', {
        'facebook_login': facebook_login,
        'can_disconnect': can_disconnect
    })


@login_required
def home(request):
    followings = request.user.followings.all()
    return render(request, 'home.html', {'followings': followings})


@login_required
def follow(request):
    data = dict()
    target_pk = request.POST.get('target_pk')
    target = get_object_or_404(User, pk=target_pk)
    if request.method == 'POST':
        if not request.user.followings.filter(followed=target).exists():
            Follow.objects.create(
                followed=target,
                follower=request.user,
                followed_at=timezone.now()
            )
            data['is_followed'] = True 
            data['follow'] = "following"
        else:
            request.user.followings.filter(followed=target).delete()
            data['is_followed'] = False 
            data['follow'] = "Follow"
    data['followers_count'] = str(target.followers.all().count())
    data['username'] = target.username 
    return JsonResponse(data)


@login_required
@require_POST
def like(request):
    data = {}
    if request.method == 'POST':
        story_pk = request.POST.get('story_pk')
        try:
            story = Story.objects.get(pk=story_pk)     
        except Story.DoesNotExist:
            story = None 

        if story.likes.filter(liker=request.user).exists():
            story.likes.filter(liker=request.user).delete()
            data['is_liked'] = False
        else:
            Like.objects.create(
                story=story,
                liker=request.user,
                liked_at=timezone.now()
            )
            data['is_liked'] = True 
    data['likes_count'] = str(story.get_total_likes()) + " likes"
    return JsonResponse(data)


@login_required
def search(request):
    data = dict()
    obj = request.GET.get('q')
    if obj:
        users = User.objects.filter(username__icontains=str(obj))
    else:
        users = User.objects.all().order_by('date_joined')

    if request.is_ajax():
        html_results = render_to_string('partial_search_results.html', {
            'users': users,
            'obj': obj
        })
        data['html_results'] = html_results
        return JsonResponse(data)
    return render(request, 'search.html', {'users': users})


@login_required
def new_comment(request):
    data = dict()
    story_pk = request.POST.get('story_pk')
    story = get_object_or_404(Story, pk=story_pk)

    if request.method == 'POST':
        text = request.POST.get('text')
        Comment.objects.create(
            written_by=request.user,
            written_at=timezone.now(),
            text=text,
            story=story 
        )
        data['comment_is_valid'] = True 
        comments = story.comments.all()
        data['partial_comments_list'] = render_to_string('partial_comments_list.html', {
            'comments': comments 
        })
        
    return JsonResponse(data)


@login_required
def comment(request, pk):
    story = get_object_or_404(Story, pk=pk)
    queryset = story.comments.all().order_by('-written_at')
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page', 1)
    try:
        comments = paginator.page(page)
    except (EmptyPage, InvalidPage):
        comments = paginator.page(paginator.num_pages)
    return render(request, 'comments.html', {'story': story, 'comments': comments})  


@login_required
def profile(request, pk):
    data = dict()
    profile_user = get_object_or_404(User, pk=pk)
    if request.is_ajax():
        data['html_profile'] = render_to_string('partial_profile_template.html', {
            'profile_user': profile_user
        })
        return JsonResponse(data)
        
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile', kwargs={'pk': request.user.pk}))
    else:
        form = ProfilePhotoForm(instance=request.user.profile)
    return render(request, 'profile.html', {'profile_user': profile_user, 'form': form})


@login_required
def story(request):
    stories = request.user.stories.all()
    return render(request, 'new_story.html', {'stories': stories})


@login_required
def new_story(request):
    data = dict()
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.posted_at = timezone.now()
            story.posted_by = request.user 
            story.save()
            data['form_is_valid'] = True
            stories = request.user.stories.all()
            data['html_stories'] = render_to_string('partial_stories_template.html', {
                'updated_stories': updated_stories 
            })
        else:
            data['form_is_valid'] = False 
        return JsonResponse(data)
    else:
        form = StoryForm()
    return render(request, 'new_story.html', {'form': form, 'stories': request.user.stories.all()})


@login_required
def post_story(request):
    data = dict()
    ImageFormSet = modelformset_factory(Image, form=ImageForm, extra=10)
    if request.method == 'POST':
        story_form = StoryForm(request.POST)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if story_form.is_valid() and formset.is_valid():
            story = story_form.save(commit=False)
            story.posted_by = request.user 
            story.posted_at = timezone.now()
            story.save()
            for form in formset.cleaned_data:
                if form:
                    image = form['file']
                    photo = Image(story=story, file=image)
                    photo.save()
            data['form_is_valid'] = True
            data['message'] = "%s photos posted to your story" % (len(request.FILES))
            stories = request.user.stories.all().order_by('-posted_at')[:10]
            data['html_stories'] = render_to_string('partial_stories_template.html', {'stories': stories})
        else:
            data['form_is_valid'] = False 
            data['message']  = "An error occured while trying to post the images"
        return JsonResponse(data)
    else:
        story_form = StoryForm()
        formset = ImageFormSet(queryset=Image.objects.none())
    return render(request, 'post_story.html', {'story_form': story_form, 'formset': formset})   


@login_required
def toggle_account_privacy(request):
    data = dict()
        
    if request.method == 'POST':
        if request.user.account.is_private == True:
            request.user.account.is_private = False 
            data['account_is_private'] = False 
        else:
            request.user.account.is_private = True 
            data['account_is_private'] = True 
        request.user.save()
    return JsonResponse(data)


def post(request):
    data = dict()
    if request.method == 'POST':
        caption_text = request.POST.get('caption_text', None)
        files = request.POST.getlist('files')
        story = Story(
            posted_at=timezone.now(),
            posted_by=request.user,
            text=caption_text
        )
        story.save()
        for file in files:
            Image.objects.create(
                story=story,
                created_at=story.posted_at,
                file=file
            )
        data['story-posted'] = True
        data['message'] = "{number} posted to timeline".format(len(request.FILES))
        data['html_images'] = render_to_string('partial-story-images.html', {'images': story.images.all()})
        return JsonResponse(data)
    return render(request, 'post.html')


    
