import datetime
from django.shortcuts import render
from django.http import HttpResponse
from article.models import Article
from article.models import Category
from article.models import Issue
from article import forms
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect

def homepage(request):
  return listarticles(request, None, None, None)

def issue(request, year, month):
  return listarticles(request, None, year, month)

def submit(request):
  categories = Category.objects.all()
  issues = Issue.objects.all()

  if request.method == "POST":
    form = forms.Submit(request.POST)
    if form.is_valid():
      article = Article()
      article.title = form.cleaned_data["title"].strip()
      article.author = form.cleaned_data["author"].strip()
      # TODO email = form.cleaned_data["email"]
      article.content = form.cleaned_data["content"]
      article.date = datetime.date.today()
      article.save()
      return HttpResponseRedirect("/")
  else: # "GET"
    form = forms.Submit()

  templatearguments = {
    "categories" : categories,
    "issues" : issues,
    "form" : form,
    "cancel_url" : "/",
  }
  return render(request, 'article/submit.html', templatearguments)

def _example_submit(request):
  if request.method == "POST":
    form = forms.CreateBounty(request.POST)
    if form.is_valid():
      bounty = control.create(
        request.user,
        form.cleaned_data["title"].strip(),
        form.cleaned_data["description"].strip(),
        form.cleaned_data["tags"].strip(),
        form.cleaned_data["target"],
        form.cleaned_data["deadline"]
      )
      return HttpResponseRedirect(bounty.url_funds)
  else:
    form = forms.CreateBounty()
  args = {
    "form" : form, "form_title" : _("CREATE_BOUNTY"),
    "cancel_url" : "/",
    "navbar_active" : "CREATE",
  }
  return render_response(request, 'site/form.html', args)



def listarticles(request, category_slug, year, month):
  articles = Article.objects.all()
  categories = Category.objects.all()
  issues = Issue.objects.all()

  currentcategory = None
  if not category_slug:
    articles = articles.filter(featured=True)
  else:
    for category in categories:
      if category.slug() == category_slug:
        currentcategory = category
    if not currentcategory:
      raise Http404
    articles = articles.filter(category=currentcategory)

  currentissue = None
  if month and year:
    currentissue = get_object_or_404(Issue, month=int(month), year=int(year))
  else:
    currentissue = Issue.objects.all()[0]
  articles = articles.filter(issue=currentissue)

  templatearguments = {
    "articles" : articles,
    "categories" : categories,
    "issues" : issues,
    "currentcategory" : currentcategory,
    "currentissue" : currentissue,
  }
  return render(request, 'article/homepage.html', templatearguments)

def displayarticle(request, id):
  article = get_object_or_404(Article, id=id)
  categories = Category.objects.all()
  issues = Issue.objects.all()
  currentissue = article.issue
  currentcategory = article.category
  templatearguments = {
    "article" : article,
    "categories" : categories,
    "issues" : issues,
    "currentcategory" : currentcategory,
    "currentissue" : currentissue,
  }
  return render(request, 'article/article.html', templatearguments)

