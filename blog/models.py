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

from django.db import models
from django.urls import reverse
from django.conf import settings as project_settings
from datetime import datetime, timedelta
from . import settings
import os
import re

class UserLevel():
    FULL = 0
    COLLABORATOR = 1
    VISITOR = 2

class Tag(models.Model):
    name = models.CharField(max_length=50)
    uid = models.CharField(max_length=50)
    
    def to_dict(self):
        return {
            "pk": self.pk,
            "name": self.name,
            "uid": self.uid,
        }
    
    def from_dict(self, data):
        self.pk = data['pk']
        self.name = data['name']
        self.uid = data['uid']
        
        self.save()

class User(models.Model):
    name = models.CharField(max_length=50)
    oauth2_id = models.CharField(max_length=100)
    session_id = models.CharField(max_length=32)
    level = models.IntegerField(default=UserLevel.VISITOR)
    username = models.CharField(max_length=50)
    email = models.CharField(max_length=100)
    picture_url = models.CharField(max_length=100)
    bio = models.TextField(default="")
    blocked = models.BooleanField(default=False)
    hide_content = models.BooleanField(default=False)
    hide_picture = models.BooleanField(default=False)
    
    def update_session_id(self, response):
        self.session_id = os.urandom(16).hex()
        self.save()
        
        response.set_cookie(
            "session_id",
            value = self.username + "=" + self.session_id,
            expires = datetime.utcnow() + timedelta(days=30),
            secure = (not project_settings.DEBUG),
            httponly = True
        )
    
    def to_dict(self):
        return {
            "pk": self.pk,
            "name": self.name,
            "oauth2_id": self.oauth2_id,
            "level": self.level,
            "username": self.username,
            "email": self.email,
            "picture_url": self.picture_url,
            "bio": self.bio,
            "blocked": self.blocked,
            "hide_content": self.hide_content,
            "hide_picture": self.hide_picture,
        }
    
    def from_dict(self, data):
        self.pk = data['pk']
        self.name = data['name']
        self.oauth2_id = data['oauth2_id']
        self.level = data['level']
        self.username = data['username']
        self.email = data['email']
        self.picture_url = data['picture_url']
        self.bio = data['bio']
        self.blocked = data['blocked']
        self.hide_content = data['hide_content']
        self.hide_picture = data['hide_picture']
        
        self.save()
    
    def PAGE_WRITE(self):
        return self.level in [UserLevel.FULL]
    
    def USER_WRITE(self):
        return self.level in [UserLevel.FULL]
    
    def POST_WRITE(self):
        return self.level in [UserLevel.FULL, UserLevel.COLLABORATOR]
    
    def COMMENT_DELETE(self):
        return self.level in [UserLevel.FULL, UserLevel.COLLABORATOR]
    
    def COMMENT_WRITE(self):
        return self.level in [UserLevel.FULL, UserLevel.COLLABORATOR, UserLevel.VISITOR] and not self.blocked
    
    def LEVEL_FULL(self):
        return self.level == UserLevel.FULL

class Comment(models.Model):
    author = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name="comments")
    body = models.TextField()
    date = models.DateTimeField(default=datetime.utcnow)
    hidden = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    
    def to_dict(self):
        return {
            "author": self.author.pk,
            "body": self.body,
            "date": self.date,
            "hidden": self.hidden,
            "deleted": self.deleted,
        }
    
    def from_dict(self, data):
        self.author = User.objects.get(pk=data['author'])
        self.body = data['body']
        self.date = data['date']
        self.hidden = data['hidden']
        self.deleted = data['deleted']
        
        self.save()

class File(models.Model):
    name = models.CharField(max_length=100)
    content = models.BinaryField()

class Post(models.Model):
    uid = models.CharField(max_length=150)
    title = models.CharField(max_length=150)
    body = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts")
    authors = models.ManyToManyField(User, related_name="posts")
    draft = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    date = models.DateTimeField(default=datetime.utcnow)
    edit_date = models.DateTimeField(default=datetime.utcnow)
    files = models.ManyToManyField(File, related_name="+")
    comments = models.ManyToManyField(Comment, related_name="+")
    
    def body_preview(self):
        tmp = re.sub('src="(?!(http://)|(https://))',
                     'src="{}{}'.format(project_settings.SECURE_SITE_URL, reverse('post', kwargs={
                         "year": self.date.year,
                         "month": self.date.strftime('%m'),
                         "uid": self.uid})),
                     self.body)
        return re.sub('href="(?!(http://)|(https://))',
                      'href="{}{}'.format(project_settings.SECURE_SITE_URL, reverse('post', kwargs={
                          "year": self.date.year,
                          "month": self.date.strftime('%m'),
                          "uid": self.uid})),
                      tmp)
    
    def to_dict(self):
        return {
            "pk": self.pk,
            "uid": self.uid,
            "title": self.title,
            "body": self.body,
            "tags": list((tag.pk for tag in self.tags.all())),
            "authors": list((author.pk for author in self.authors.all())),
            "draft": self.draft,
            "allow_comments": self.allow_comments,
            "date": self.date,
            "edit_date": self.edit_date,
            "files": list((f.name for f in self.files.all())),
            "comments": list((comment.to_dict() for comment in self.comments.all())),
        }
    
    def from_dict(self, data):
        self.pk = data['pk']
        self.uid = data['uid']
        self.title = data['title']
        self.body = data['body']
        self.draft = data['draft']
        self.allow_comments = data['allow_comments']
        self.date = data['date']
        self.edit_date = data['edit_date']
        
        self.save()
        
        for tag_pk in data['tags']:
            self.tags.add(Tag.objects.get(pk=tag_pk))
        
        for author_pk in data['authors']:
            self.authors.add(User.objects.get(pk=author_pk))
        
        for comment_dict in data['comments']:
            comment = Comment()
            comment.from_dict(comment_dict)
            comment.save()
            self.comments.add(comment)
        
        self.save()

class Page(models.Model):
    uid = models.CharField(max_length=150)
    title = models.CharField(max_length=150)
    body = models.TextField()
    files = models.ManyToManyField(File, related_name="+")
    edit_date = models.DateTimeField(auto_now=True)
    
    def to_dict(self):
        return {
            "pk": self.pk,
            "uid": self.uid,
            "title": self.title,
            "body": self.body,
            "files": list((f.name for f in self.files.all())),
            "edit_date": self.edit_date,
        }
    
    def from_dict(self, data):
        self.pk = data['pk']
        self.uid = data['uid']
        self.title = data['title']
        self.body = data['body']
        self.edit_date = data['edit_date']
        
        self.save()
