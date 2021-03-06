import uuid
import datetime
from decimal import Decimal
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from config import settings
from support.forms import Support
from article.models import Article, Category, Issue
from page.models import Page
from article import forms
from comment import forms as comment_forms
from comment import models as comment_models
from photologue.models import Gallery

def chunks(items, size): # TODO put in common
  return [items[i:i+size] for i in range(0, len(items), size)]

def baskets(items, count): # TODO put in common
  _baskets = [[] for _ in range(count)]
  for i, item in enumerate(items):
    _baskets[i % count].append(item)
  return filter(None, _baskets) 

def previewlistformat(items):
  pages = chunks(items, 10)
  return map(lambda page: {'columns' : baskets(page,2), 'items' : page}, pages)

def submit(request):

  if request.method == "POST":
    form = forms.Submit(request.POST)
    if form.is_valid():
      article = Article()
      article.title = form.cleaned_data["title"].strip()
      article.author = form.cleaned_data["author"].strip()
      article.email = form.cleaned_data["email"].strip()
      article.content = form.cleaned_data["content"]
      article.coverletter = form.cleaned_data["coverletter"]
      article.save()
      submitted_page = get_object_or_404(Page, title="Article Submitted")
      return HttpResponseRedirect(submitted_page.url())
  else: # "GET"
    form = forms.Submit()

  guidelines = get_object_or_404(Page, title="Submission Guidelines")
  templatearguments = {
    "generic_form" : {
      "title" : "Submit Article",
      "markdown_info" : guidelines.content,
      "form" : form,
      "cancel_url" : "/",
    }
  }
  return render(request, 'common/submit.html', templatearguments)

@login_required
def edit(request, article_id):
  if not request.user.is_superuser:
    raise PermissionDenied

  article = get_object_or_404(Article, id=article_id)

  if request.method == "POST":
    form = forms.Edit(request.POST, article=article)
    if form.is_valid():
      article.title = form.cleaned_data["title"].strip()
      article.author = form.cleaned_data["author"].strip()
      article.preview = form.cleaned_data["preview"]
      article.content = form.cleaned_data["content"]
      article.coverletter = form.cleaned_data["coverletter"]
      article.category = form.cleaned_data["category"]
      article.featured = form.cleaned_data["featured"]
      article.date = form.cleaned_data["date"]
      article.save()
      return HttpResponseRedirect(article.url())
  else: # "GET"
    form = forms.Edit(article=article)

  templatearguments = {
    "generic_form" : {
      "title" : "Edit Article",
      "cancel_url" : article.url(),
      "form" : form,
    }
  }
  return render(request, 'common/submit.html', templatearguments)

def sitegallery(request):
  gallery = get_object_or_404(Gallery, title="sitegallery")
  sitegalleryphotos = gallery.photos.all()
  sitegallerydata = previewlistformat(sitegalleryphotos)
  templatearguments = { 
      'sitegallerydata' : sitegallerydata,
      'caruseltitle' : 'Gallery'
  }
  return render(request, 'article/sitegallery.html', templatearguments)

def archive(request):
  issues = Issue.objects.filter(published=True).exclude(pdf=None)
  templatearguments = { 'issues' : issues }
  return render(request, 'article/archive.html', templatearguments)

def listing(request, category_slug):

  articles = Article.objects.all()
  if not request.user.is_superuser:
    today = datetime.datetime.now().date()
    articles = articles.exclude(date=None).filter(date__lte=today)

  # category
  currentcategory = None
  if not category_slug or category_slug in ["featured", "home"]:
    articles = articles.filter(featured=True)
  else: # show category articles
    for category in Category.objects.all():
      if category.slug() == category_slug:
        currentcategory = category
    if not currentcategory:
      raise Http404
    articles = articles.filter(category=currentcategory)

  articlesdata = previewlistformat(articles)
  templatearguments = {
    "articlesdata" : articlesdata,
    "currentcategory" : currentcategory
  }
  return render(request, 'article/listing.html', templatearguments)


def display(request, article_id):
  article = get_object_or_404(Article, id=article_id)
  if(not article.published() and not request.user.is_superuser):
    raise PermissionDenied

  if request.method == "POST":
    support_form = Support(request.POST)
    comment_form = comment_forms.Comment(request.POST)

    if comment_form.is_valid():
      comment = comment_models.Comment()
      comment.alias = comment_form.cleaned_data["alias"].strip()
      comment.content = comment_form.cleaned_data["content"].strip()
      comment.save()
      article.comments.add(comment)
      return HttpResponseRedirect(article.url())

    if support_form.is_valid():
      amount = support_form.cleaned_data["amount"]
      ratio = support_form.cleaned_data["ratio"] / Decimal("100.0")
      url = "/support/%s/%.2f/%.2f/%s.html" % (
          article.id, amount, ratio, article.title_slug()
      )
      return HttpResponseRedirect(url)

  else: # "GET"
    support_form = Support()
    comment_form = comment_forms.Comment()

  templatearguments = {
    "article" : article,
    "currentcategory" : article.category,

    "comment_form" : {
      "title" : "Create comment",
      'form' : comment_form,
      "submit_label" : "Post comment",
      'submit_class' : "btn btn-success",
    },

    "support_form" : {
      "title" : "Support the author",
      'form' : support_form,
      "submit_label" : "Continue",
      'submit_class' : "btn btn-success",
    },
  }
  return render(request, 'article/display.html', templatearguments)

