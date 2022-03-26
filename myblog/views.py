import os
# from newsapi import NewsApiClient
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.core.paginator import Paginator
from .models import Post, Comment
from .forms import SignUpForm, SignInForm, FeedBackForm, CommentForm
from django.contrib.auth import login, authenticate
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import send_mail, BadHeaderError
from django.db.models import Q
from taggit.models import Tag


class SignUpView(View):
    def get(self, request, *args, **kwargs):
        form = SignUpForm()
        return render(request, 'myblog/signup.html', context={'form': form, })

    def post(self, request, *args, **kwargs):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user is not None:
                login(request, user)  # логинем пользователя
                return HttpResponseRedirect('/')
        return render(request, 'myblog/signup.html', context={'form': form, })


class SignInView(View):
    def get(self, request, *args, **kwargs):
        form = SignInForm()
        return render(request, 'myblog/signin.html', context={'form': form, })

    def post(self, request, *args, **kwargs):
        form = SignInForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = form.cleaned_data['password']  # безопаснее для хранения в БД
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')
        return render(request, 'myblog/signin.html', context={'form': form, })


class FeedBackView(View):
    def get(self, request, *args, **kwargs):
        form = FeedBackForm()
        return render(request, 'myblog/contact.html', context={'title': 'Свяжитесь со мной', 'form': form})

    def post(self, request, *args, **kwargs):
        form = FeedBackForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            from_email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            try:
                send_mail(f'От {name} | {subject}', message, from_email, ['nikkres@mail.ru'])
            except BadHeaderError:
                return HttpResponse('Невалидный заголовок')
            return HttpResponseRedirect('success')
        return render(request, 'myblog/contact.html', context={'form': form, })


class SearchResultsView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q')
        results = ''
        if query:
            results = Post.objects.filter(Q(h1__icontains=query) | Q(content__icontains=query))
        paginator = Paginator(results, 6)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'myblog/search.html', context={'results': page_obj, 'count': paginator.count})


class SuccessView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'myblog/success.html', )


class MainView(View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all()
        paginator = Paginator(posts, 6)

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'myblog/index.html', context={'page_obj': page_obj})


class PostDetailView(View):
    def get(self, request, slug_url, *args, **kwargs):
        post = get_object_or_404(Post, url=slug_url)
        common_tags = Post.tag.most_common()
        last_posts = Post.objects.all().order_by('-id')[:3]
        comment_form = CommentForm()
        return render(request, 'myblog/post_detail.html', context={
            'post': post,
            'common_tags': common_tags,
            'last_posts': last_posts,
            'comment_form': comment_form
        })

    def post(self, request, slug_url, *args, **kwargs):
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            text = request.POST['text']
            username = self.request.user
            post = get_object_or_404(Post, url=slug_url)
            Comment.objects.create(post=post, username=username, text=text)
            return HttpResponseRedirect(
                request.META.get('HTTP_REFERER', '/'))  # редирект на страницу на который находился до этого
        return render(request, 'myblog/post_detail.html', context={'comment_form': comment_form})


class TagView(View):
    def get(self, request, slug_tag, *args, **kwargs):
        tag = get_object_or_404(Tag, slug=slug_tag)
        posts = Post.objects.filter(tag__in=[tag])
        common_tags = Post.tag.most_common()
        return render(request, 'myblog/tag.html',
                      context={'title': f'{tag}', 'posts': posts, 'common_tags': common_tags})

# class News(View):
#     def get(self, request, *args, **kwargs):
#         APIKEY = os.getenv('APIKEY')
#         newsapi = NewsApiClient(api_key=APIKEY)
#         top = newsapi.get_top_headlines(sources='techcrunch')
#
#         l = top['articles']
#         dsc = []
#         nws = []
#         im = []
#
#         for i in range(len(l)):
#             f = l[i]
#             nws.append(f['title'])
#             dsc.append(f['description'])
#             im.append(f['urlToImage'])
#             mylist = zip(nws, dsc, im)
#
#         return render(request, 'myblog/index.html', context={"mylist": mylist})
