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

from django.conf.urls import url

from . import views

urlpatterns = [
    url('^$', views.index, name='index'),
    url('^posts/(?P<page_number>[0-9]{1,})/$', views.index, name="index"),
    url('^author/(?P<username>[a-zA-Z0-9_.-]{1,})/$', views.author, name="author"),
    url('^author/(?P<username>[a-zA-Z0-9_.-]{1,})/(?P<page_number>[0-9]{1,})/$', views.author, name="author"),
    url('^tag/(?P<tag_uid>[a-zA-Z0-9_.-]{1,})/$', views.tag, name="tag"),
    url('^tag/(?P<tag_uid>[a-zA-Z0-9_.-]{1,})/(?P<page_number>[0-9]{1,})/$', views.tag, name="tag"),
    url('^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<uid>[a-z0-9-]{1,})/$', views.post, name="post"),
    url('^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<uid>[a-z0-9-]{1,})/(?P<filename>[a-zA-Z0-9_.-]{1,})$', views.post_file, name="post_file"),
    url('^submit_comment/(?P<pk>[0-9]{1,})/$', views.submit_comment, name="submit_comment"),
    url('^toggle_delete_comment/(?P<pk>[0-9]{1,})/$', views.toggle_delete_comment, name="toggle_delete_comment"),
    url('^page/(?P<uid>[a-z0-9-]{1,})/$', views.page, name="page"),
    url('^page/(?P<uid>[a-z0-9-]{1,})/(?P<filename>[a-zA-Z0-9_.-]{1,})$', views.page_file, name="page_file"),
    url('^feed/$', views.feed, name="feed"),
    url('^tag/(?P<tag_uid>[a-zA-Z0-9_.-]{1,})/feed/$', views.feed, name="tag_feed"),
    url('^author/(?P<username>[a-zA-Z0-9_.-]{1,})/feed/$', views.feed, name="author_feed"),
    #login
    url('^oauth2_login/(?P<provider>[a-z]{1,})/$', views.oauth2_login, name="oauth2_login"),
    url('^oauth2callback/(?P<provider>[a-z]{1,})/$', views.oauth2callback, name="oauth2callback"),
    url('^logout/$', views.logout, name='logout'),
    #admin
    url('^admin/one_time_elevation/$', views.admin_one_time_elevation, name='admin_one_time_elevation'),
    url('^admin/posts_overview/$', views.admin_posts_overview, name='admin_posts_overview'),
    url('^admin/pages_overview/$', views.admin_pages_overview, name='admin_pages_overview'),
    url('^admin/users_overview/$', views.admin_users_overview, name='admin_users_overview'),
    url('^admin/edit_post/$', views.admin_edit_post, name='admin_edit_post'),
    url('^admin/edit_page/$', views.admin_edit_page, name='admin_edit_page'),
    url('^admin/delete_file/(?P<doc_type>[a-z]{1,})/(?P<pk>[0-9]{1,})/(?P<filename>[a-zA-Z0-9_.-]{1,})/$', views.admin_delete_file, name='admin_delete_file'),
]
