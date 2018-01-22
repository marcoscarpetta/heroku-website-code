#
# Copyright (C) 2017-2018 Marco Scarpetta
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from django.shortcuts import render, redirect, get_object_or_404
from django.core.validators import URLValidator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings as project_settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from datetime import datetime, timedelta
import requests
import json
import os
import unicodedata
import re
import mimetypes
import bleach
import zipfile
import io
import ruamel.yaml as yaml

from . import models
from . import settings

def str_presenter(dumper, value):
    if "\n" in value:
        value = value.replace("\r\n", "\n")
        return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style="|")
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, "\"")

yaml.add_representer(str, str_presenter)

oauth2_parameters = {
    "google": {
        "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://www.googleapis.com/oauth2/v4/token",
        "scopes": "email%20https://www.googleapis.com/auth/userinfo.profile",
        "profile_api_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "id": "sub",
        "name": "name",
        "email": "email",
        "picture_url": "picture"
    },
    "github": {
        "client_id": settings.GITHUB_OAUTH2_CLIENT_ID,
        "client_secret": settings.GITHUB_OAUTH2_CLIENT_SECRET,
        "auth_uri": "https://github.com/login/oauth/authorize",
        "token_uri": "https://github.com/login/oauth/access_token",
        "scopes": "user",
        "profile_api_url": "https://api.github.com/user",
        "id": "id",
        "name": "name",
        "email": "email",
        "picture_url": "avatar_url"
    },
}

def pretty_title(title, words_number=5, separator='-'):
    title = unicodedata.normalize('NFKD', title)
    title = title.lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789 "
    title = "".join(l for l in title if l in allowed)
    
    words = [word for word in title.split(" ") if word != ""]
    
    if len(words) == 0:
        return "untitled"
    
    pretty_title = ""
    for word in words:
        pretty_title += word + separator
    
    return pretty_title[:-1]
    
def redirect_to_secure(request):
    if not request.is_secure() and project_settings.DEBUG == False:
        return redirect(request.url.replace(project_settings.SITE_URL, project_settings.SECURE_SITE_URL))

def get_logged_user(request):
    if "session_id" in request.COOKIES and (request.is_secure() or project_settings.DEBUG == True):
        user_session_id = request.COOKIES.get("session_id").split("=")
        if len(user_session_id) == 2 and len(user_session_id[1]) == 32:
            try:
                user = models.User.objects.get(username=user_session_id[0])
                if user.session_id == user_session_id[1]:
                    return user
            except:
                pass
    
    return None

def index(request, page_number=0):
    logged_user = get_logged_user(request)
    
    ppp = settings.POSTS_PER_PAGE
    posts_count = models.Post.objects.filter(draft__exact=False).count()
    context = {
        "page_number": page_number,
        "logged_user": logged_user,
    }
    page_number = int(page_number)
    
    if posts_count > ppp*page_number:
        context["posts"] = models.Post.objects.filter(draft__exact=False).order_by('-date')[ppp*page_number:ppp*(page_number+1)]
        
        if page_number > 0:
            context["next_posts"] = page_number - 1
        if posts_count > ppp*(page_number+1):
            context["prev_posts"] = page_number + 1
    
    response = render(request, "blog/index.html", context)
    
    if logged_user:
        logged_user.update_session_id(response)
    
    return response

def author(request, username, page_number=0):
    logged_user = get_logged_user(request)
    
    author = get_object_or_404(models.User, username=username)
    
    context = {
        "author": author,
        "page_number": page_number,
        "logged_user": logged_user,
    }
    page_number = int(page_number)
    
    ppp = settings.POSTS_PER_PAGE
    posts_count = author.posts.filter(draft__exact=False).count()
    
    if posts_count > ppp*page_number:
        context["posts"] = author.posts.filter(draft__exact=False).order_by('-date')[ppp*page_number:ppp*(page_number+1)]
        
        if page_number > 0:
            context["next_posts"] = page_number - 1
        if posts_count > ppp*(page_number+1):
            context["prev_posts"] = page_number + 1
    
    response = render(request, "blog/author.html", context)
    
    if logged_user:
        logged_user.update_session_id(response)
    
    return response

def tag(request, tag_uid, page_number=0):
    logged_user = get_logged_user(request)
    
    tag = get_object_or_404(models.Tag, uid=tag_uid)
    
    context = {
        "tag": tag,
        "page_number": page_number,
        "logged_user": logged_user,
    }
    
    page_number = int(page_number)
    
    ppp = settings.POSTS_PER_PAGE
    posts_count = tag.posts.filter(draft__exact=False).count()
    
    if posts_count > ppp*page_number:
        context["posts"] = tag.posts.filter(draft__exact=False).order_by('-date')[ppp*page_number:ppp*(page_number+1)]
        
        if page_number > 0:
            context["next_posts"] = page_number - 1
        if posts_count > ppp*(page_number+1):
            context["prev_posts"] = page_number + 1
    
    response = render(request, "blog/tag.html", context)
    
    if logged_user:
        logged_user.update_session_id(response)
    
    return response

def post(request, year, month, uid):
    logged_user = get_logged_user(request)
    
    try:
        post = models.Post.objects.filter(date__year=int(year), date__month=int(month)).get(uid=uid)
    except:
        raise Http404()
        
    response = render(request, "blog/post.html", context={
        "post": post,
        "logged_user": logged_user
    })
    
    if logged_user:
        logged_user.update_session_id(response)
    
    return response

def post_file(request, year, month, uid, filename):
    try:
        post = models.Post.objects.filter(date__year=int(year), date__month=int(month)).get(uid=uid)
        f = post.files.all().get(name=filename)
        
        response = HttpResponse(content=f.content)
        response['Content-Type'] = mimetypes.guess_type(f.name)
        return response
    
    except:
        raise Http404()

def submit_comment(request, pk):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.COMMENT_WRITE() and request.method == "POST":
        post = get_object_or_404(models.Post, pk=int(pk))
        
        comment = models.Comment()
        comment.author = logged_user
        comment.date = datetime.utcnow()
        comment.body = bleach.clean(request.POST["comment"],
                                    tags=['a', 'b', 'i'],
                                    attributes={'a': ['href', 'title']})
        comment.save()
        
        post.comments.add(comment)
        
        response = redirect(request.META['HTTP_REFERER'], code=302)
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def toggle_delete_comment(request, pk):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.COMMENT_WRITE():
        comment = get_object_or_404(models.Comment, pk=int(pk))
        
        if comment.author == logged_user:
            comment.deleted = not comment.deleted
            comment.save()
            response = redirect(request.META['HTTP_REFERER'], code=302)
            logged_user.update_session_id(response)
            return response
    
    raise PermissionDenied()
        
def page(request, uid):
    page = get_object_or_404(models.Page, uid=uid)
    logged_user = get_logged_user(request)
        
    return render(request, "blog/page.html", context={
        "page": page,
        "logged_user": logged_user
    })
    
    if logged_user:
        logged_user.update_session_id(response)
    
    return response

def page_file(request, uid, filename):
    try:
        page = models.Page.objects.get(uid=uid)
        f = page.files.all().get(name=filename)
        
        response = HttpResponse(content=f.content)
        response['Content-Type'] = mimetypes.guess_type(f.name)
        return response
    
    except:
        raise Http404()

def feed(request, tag_uid=None, username=None):
    context = {}
    
    if username:
        author = get_object_or_404(models.User, username=username)
        context["posts"] = author.posts.filter(draft__exact=False).order_by('-date')[0:settings.ATOM_POSTS]
    elif tag_uid:
        tag = get_object_or_404(models.Tag, uid=tag_uid)
        context["posts"] = tag.posts.filter(draft__exact=False).order_by('-date')[0:settings.ATOM_POSTS]
    else:
        context["posts"] = models.Post.objects.filter(draft__exact=False).order_by('-date')[0:settings.ATOM_POSTS]
    
    context["updated"] = datetime.utcnow() if len(context["posts"]) == 0 else context["posts"][0].date
    
    return render(request, "blog/atom.xml", context, content_type="application/atom+xml")

def oauth2_login(request, provider):
    redirect_to_secure(request)

    client_secrets = oauth2_parameters[provider]
    
    state = os.urandom(32).hex()
    
    response = redirect(
        client_secrets["auth_uri"] + \
        "?client_id=" + client_secrets["client_id"] + \
        "&response_type=code&scope=" + client_secrets["scopes"] + \
        "&redirect_uri=" + project_settings.SECURE_SITE_URL + reverse('oauth2callback', kwargs={"provider": provider}) + \
        "&state=" + state,
        code=302
    )
    
    response.set_cookie("state",
                        value=state,
                        expires=datetime.utcnow() + timedelta(seconds=120),
                        secure=(not project_settings.DEBUG),
                        httponly=True)
    
    response.set_cookie("source_url",
                        value=request.GET["source_url"],
                        expires=datetime.utcnow() + timedelta(seconds=120),
                        secure=(not project_settings.DEBUG),
                        httponly=True)
    
    return response

def oauth2callback(request, provider):
    redirect_to_secure(request)
    
    client_secrets = oauth2_parameters[provider]
    
    if request.COOKIES.get("state") == request.GET["state"]:
        r = requests.post(
            client_secrets["token_uri"],
            data = {
                "code": request.GET["code"],
                "client_id": client_secrets["client_id"],
                "client_secret": client_secrets["client_secret"],
                "redirect_uri": project_settings.SECURE_SITE_URL + reverse('oauth2callback', kwargs={"provider": provider}),
                "grant_type": "authorization_code",
                "state": request.COOKIES.get("state")
            },
            headers = {"Accept": "application/json"}
        )
        
        access_token = json.loads(r.text)["access_token"]
        
        r = requests.get(client_secrets["profile_api_url"] + \
            "?access_token=" + access_token)
        
        userinfo = json.loads(r.text)
        
        oauth2_id = "{}@{}".format(userinfo[client_secrets["id"]], provider)
        
        try:
            # Get existing url
            user = models.User.objects.get(oauth2_id=oauth2_id)
            # Update user's profile picture url on each login
            user.picture_url = userinfo[client_secrets["picture_url"]]
        except:
            # Create new user
            user = models.User()
            user.oauth2_id = oauth2_id
            user.name = userinfo[client_secrets["name"]]
            user.email = userinfo[client_secrets["email"]]
            user.picture_url = userinfo[client_secrets["picture_url"]]
            
            if provider == "github":
                r = requests.get("https://api.github.com/user/emails?access_token=" + access_token)
                emails = json.loads(r.text)
                try:
                    user.email = emails[0]["email"]
                except:
                    pass
            
            #creating username
            username = pretty_title(user.name, separator='.')
            
            if models.User.objects.filter(username=username).count() > 0:
                n = 0
                while models.User.objects.filter(username="{}{}".format(username, n)).count() > 0:
                    n += 1
                user.username = "{}{}".format(username, n)
            else:
                user.username = username

        response = redirect(request.COOKIES.get("source_url"), code=302)
        user.update_session_id(response)
        return response
    else:
        return "Error"

def admin_one_time_elevation(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    context = {"logged_user": logged_user}
    
    if logged_user:
        if request.method == "POST":
            if "password" in request.POST and request.POST["password"] == settings.ONE_TIME_ADMIN_PASSWORD:
                if models.User.objects.filter(level=models.UserLevel.FULL).count() == 0:
                    logged_user.level = models.UserLevel.FULL
                    logged_user.save()
                    
                    context["done"] = True
                else:
                    context["error_admin_existent"] = True
            else:
                context["error_wrong_password"] = True
    else:
        raise PermissionDenied()
    
    return render(request, "blog/admin_one_time_elevation.html", context)

def logout(request):
    redirect_to_secure(request)
    
    user = get_logged_user(request)
    
    if user != None:
        user.session_id = ""
        user.save()
    
    if "redirect_url" in request.GET:
        return redirect(request.GET["redirect_url"], code=302)
    else:
        return redirect(reverse("index"), code=302)

def admin_posts_overview(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.POST_WRITE():
        response = render(request, "blog/admin_posts_overview.html", {
            "logged_user": logged_user,
            "posts": models.Post.objects.order_by('-date'),
        })
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def admin_pages_overview(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.PAGE_WRITE():
        response = render(request, "blog/admin_pages_overview.html", {
            "logged_user": logged_user,
            "pages": models.Page.objects.order_by('-pk'),
        })
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def admin_users_overview(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.USER_WRITE():
        response = render(request, "blog/admin_users_overview.html", {
            "logged_user": logged_user,
            "users": models.User.objects.order_by('-pk'),
        })
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def admin_edit_post(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.POST_WRITE():
        if request.method == "GET":
            if "pk" in request.GET:
                return render(request, "blog/admin_edit_post.html", {
                    "logged_user": logged_user,
                    "post": get_object_or_404(models.Post, pk=int(request.GET["pk"])),
                })
            else:
                return render(request, "blog/admin_edit_post.html", {
                    "logged_user": logged_user,
                })
        elif request.method == "POST":
            if "pk" in request.POST:
                post = get_object_or_404(models.Post, pk=int(request.POST["pk"]))
                post.edit_date = datetime.utcnow()
            else:
                post = models.Post()
                
                uid = pretty_title(request.POST["title"])
                if models.Post.objects.filter(uid=uid).count() > 0:
                    n = 0
                    while models.Post.objects.filter(uid="{}{}".format(uid, n)).count() > 0:
                        n += 1
                    post.uid = "{}{}".format(uid, n)
                else:
                    post.uid = uid
                
                post.save()
                post.authors.add(logged_user)
                date = datetime.utcnow()
                post.date = date
                post.edit_date = date
                
            post.title = request.POST["title"]
            post.body = request.POST["body"]
            post.allow_comments = "allow_comments" in request.POST
            
            post.tags.clear()
            for tag in request.POST["tags"].split(";"):
                tag_name = re.sub("\s\s+", " ", tag.strip())
                if len(tag_name) > 0:
                    tags = models.Tag.objects.filter(name=tag_name)
                    if len(tags) > 0:
                        post.tags.add(tags[0])
                    else:
                        tag = models.Tag(name=tag_name)
                        uid = pretty_title(tag_name)
                        if models.Tag.objects.filter(uid=uid).count() > 0:
                            n = 0
                            while models.Tag.objects.filter(uid="{}{}".format(uid, n)).count() > 0:
                                n += 1
                            tag.uid = "{}{}".format(uid, n)
                        else:
                            tag.uid = uid
                        tag.save()
                        post.tags.add(tag)
            
            #update date if post is de-drafted
            if post.draft == True and "draft" not in request.POST:
                date = datetime.utcnow()
                post.date = date
                post.edit_date = date
            post.draft = "draft" in request.POST
            
            #set forced date
            if "force_date" in request.POST:
                try:
                    date = datetime.strptime(request.POST["forced_date"], "%Y-%m-%d %H:%M")
                    post.date = date
                except:
                    pass
            
            #set forced edit date
            if "force_edit_date" in request.POST:
                try:
                    date = datetime.strptime(request.POST["forced_edit_date"], "%Y-%m-%d %H:%M")
                    post.edit_date = date
                except:
                    pass
            
            #save files
            if request.FILES:
                for uploaded in request.FILES:
                    uploaded = request.FILES[uploaded]
                    f = models.File(name=uploaded.name, content=uploaded.read())
                    f.save()
                    post.files.add(f)
            
            post.save()
            
            if post.draft or request.FILES:
                response = redirect(reverse("admin_edit_post") + "?pk={}".format(post.pk), code=302)
            else:
                response = redirect(reverse("admin_posts_overview"), code=302)
            
            logged_user.update_session_id(response)
            return response

    else:
        raise PermissionDenied()

def admin_edit_page(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.POST_WRITE():
        if request.method == "GET":
            if "pk" in request.GET:
                return render(request, "blog/admin_edit_page.html", {
                    "logged_user": logged_user,
                    "page": get_object_or_404(models.Page, pk=int(request.GET["pk"])),
                })
            else:
                return render(request, "blog/admin_edit_page.html", {
                    "logged_user": logged_user,
                })
        elif request.method == "POST":
            if "pk" in request.POST:
                page = get_object_or_404(models.Page, pk=int(request.POST["pk"]))
                page.edit_date = datetime.utcnow()
            else:
                page = models.Page()
                
                uid = pretty_title(request.POST["title"])
                if models.Page.objects.filter(uid=uid).count() > 0:
                    n = 0
                    while models.Page.objects.filter(uid="{}{}".format(uid, n)).count() > 0:
                        n += 1
                    page.uid = "{}{}".format(uid, n)
                else:
                    page.uid = uid
                
                page.edit_date = datetime.utcnow()
                page.save()
                
            page.title = request.POST["title"]
            page.body = request.POST["body"]
            
            #set forced edit date
            if "force_edit_date" in request.POST:
                try:
                    date = datetime.strptime(request.POST["forced_edit_date"], "%Y-%m-%d %H:%M")
                    page.edit_date = date
                except:
                    pass
            
            #save files
            if request.FILES:
                for uploaded in request.FILES:
                    uploaded = request.FILES[uploaded]
                    f = models.File(name=uploaded.name, content=uploaded.read())
                    f.save()
                    page.files.add(f)
                
                page.save()
                return redirect(reverse("admin_edit_page") + "?pk={}".format(page.pk), code=302)
            
            page.save()
            response = redirect(reverse("admin_pages_overview"), code=302)
            logged_user.update_session_id(response)
            return response

    else:
        raise PermissionDenied()

def admin_delete_file(request, doc_type, pk, filename):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.POST_WRITE():
        if doc_type == "post":
            doc = get_object_or_404(models.Post, pk=int(pk))
        elif doc_type == "page":
            doc = get_object_or_404(models.Page, pk=int(pk))
        
        f = doc.files.all().get(name=filename)
        doc.files.remove(f)
        doc.save()
        f.delete()
        
        response = redirect(request.META['HTTP_REFERER'], code=302)
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def admin_backup_overview(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.LEVEL_FULL():
        response = render(request, "blog/admin_backup.html", {
            "logged_user": logged_user,
        })
        logged_user.update_session_id(response)
        return response
    else:
        raise PermissionDenied()

def admin_backup(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    f = io.BytesIO()
    z_f = zipfile.ZipFile(f, 'w')
    
    # Backup informations
    info = {
        "version": "1.0",
    }
    
    z_f.writestr(
        os.path.join("/info.yaml"),
        yaml.dump(info, default_flow_style=False, indent=4, block_seq_indent=2)
    )
    
    # Save posts
    posts_list = []
    for post in models.Post.objects.all():
        posts_list.append(post.pk)
        
        z_f.writestr(
            os.path.join("/posts/", str(post.pk), "index.yaml"),
            yaml.dump(post.to_dict(), default_flow_style=False, indent=4, block_seq_indent=2)
        )
        
        for post_file in post.files.all():
            z_f.writestr(
                os.path.join("/posts/", str(post.pk), post_file.name),
                post_file.content
            )
    
    z_f.writestr(
        os.path.join("/posts/index.yaml"),
        yaml.dump(posts_list, default_flow_style=False, indent=4, block_seq_indent=2)
    )

    # Save pages
    pages_list = []
    for page in models.Page.objects.all():
        pages_list.append(page.pk)
        
        z_f.writestr(
            os.path.join("/pages/", str(page.pk), "index.yaml"),
            yaml.dump(page.to_dict(), default_flow_style=False, indent=4, block_seq_indent=2)
        )
        
        for page_file in page.files.all():
            z_f.writestr(
                os.path.join("/pages/", str(page.pk), page_file.name),
                page_file.content
            )
    
    z_f.writestr(
        os.path.join("/pages/index.yaml"),
        yaml.dump(pages_list, default_flow_style=False, indent=4, block_seq_indent=2)
    )
    
    # Save tags
    tags = list((tag.to_dict() for tag in models.Tag.objects.all()))
    
    z_f.writestr(
        os.path.join("/tags.yaml"),
        yaml.dump(tags, default_flow_style=False, indent=4, block_seq_indent=2)
    )
    
    # Save users
    users = list((user.to_dict() for user in models.User.objects.all()))
    
    z_f.writestr(
        os.path.join("/users.yaml"),
        yaml.dump(users, default_flow_style=False, indent=4, block_seq_indent=2)
    )
        
    z_f.close()

    f.seek(0)
    
    response = HttpResponse(content=f.read())
    response['Content-Type'] = "application/zip"
    response["Content-Disposition"] = "attachment; filename=backup.zip"
    
    return response

def admin_restore_backup(request):
    redirect_to_secure(request)
    logged_user = get_logged_user(request)
    
    if logged_user and logged_user.LEVEL_FULL():
        if request.method == "POST":
            if request.FILES and len(request.FILES) > 0:
                z_f = zipfile.ZipFile(request.FILES["backup_file"])
                
                info = yaml.safe_load(z_f.open("/info.yaml", "r").read())
                if info['version'] == "1.0":
                    # Clear database
                    models.Page.objects.all().delete()
                    models.Post.objects.all().delete()
                    models.Tag.objects.all().delete()
                    models.User.objects.all().delete()
                    models.File.objects.all().delete()
                    models.Comment.objects.all().delete()
                    
                    # Restore tag
                    tags = yaml.safe_load(z_f.open("/tags.yaml", "r").read())
                    for tag_dict in tags:
                        tag = models.Tag()
                        tag.from_dict(tag_dict)
                    
                    # Restore users
                    users = yaml.safe_load(z_f.open("/users.yaml", "r").read())
                    for user_dict in users:
                        user = models.User()
                        user.from_dict(user_dict)
                    
                    # Restore posts
                    posts_list = yaml.safe_load(z_f.open("/posts/index.yaml", "r").read())
                    for pk in posts_list:
                        post_dict = yaml.safe_load(
                            z_f.open(os.path.join("/posts/", str(pk), "index.yaml"), "r").read()
                        )
                        post = models.Post()
                        post.from_dict(post_dict)
                        
                        for filename in post_dict['files']:
                            f = models.File()
                            f.name = filename
                            f.content = z_f.open(
                                os.path.join("/posts/", str(pk), filename), "r").read()
                            f.save()
                            
                            post.files.add(f)
                        
                        post.save()
                    
                    # Restore pages
                    pages_list = yaml.safe_load(z_f.open("/pages/index.yaml", "r").read())
                    for pk in pages_list:
                        page_dict = yaml.safe_load(
                            z_f.open(os.path.join("/pages/", str(pk), "index.yaml"), "r").read()
                        )
                        page = models.Page()
                        page.from_dict(page_dict)
                        
                        for filename in page_dict['files']:
                            f = models.File()
                            f.name = filename
                            f.content = z_f.open(
                                os.path.join("/pages/", str(pk), filename), "r").read()
                            f.save()
                            
                            page.files.add(f)
                        
                        page.save()
            
        response = redirect(reverse("admin_backup_overview"), code=302)
        logged_user.update_session_id(response)
        return response

    else:
        raise PermissionDenied()
