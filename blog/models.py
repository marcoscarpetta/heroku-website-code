#
# Copyright (C) 2017 Marco Scarpetta
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

class Comment(models.Model):
    author = models.ForeignKey(User, models.SET_NULL, blank=True, null=True, related_name="comments")
    body = models.TextField()
    date = models.DateTimeField(default=datetime.utcnow)
    hidden = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

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
                      

class Page(models.Model):
    uid = models.CharField(max_length=150)
    title = models.CharField(max_length=150)
    body = models.TextField()
    files = models.ManyToManyField(File, related_name="+")
    edit_date = models.DateTimeField(auto_now=True)
