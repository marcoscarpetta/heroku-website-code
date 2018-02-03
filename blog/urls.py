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

from django.urls import path

from . import views

urlpatterns = [
    # Blog
    path('', views.index, name='index'),
    path('posts/<int:page_number>/', views.index, name="index"),
    path('author/<username>/', views.author, name="author"),
    path('author/<username>/<int:page_number>/', views.author, name="author"),
    path('tag/<tag_uid>/', views.tag, name="tag"),
    path('tag/<tag_uid>/<int:page_number>/', views.tag, name="tag"),
    path('<int:year>/<int:month>/<slug:uid>/', views.post, name="post"),
    path('<int:year>/<int:month>/<slug:uid>/<filename>/', views.post_file, name="post_file"),
    path('submit_comment/<int:pk>/', views.submit_comment, name="submit_comment"),
    path('toggle_delete_comment/<int:pk>/', views.toggle_delete_comment, name="toggle_delete_comment"),
    path('feed/', views.feed, name="feed"),
    path('tag/<tag_uid>/feed/', views.feed, name="tag_feed"),
    path('author/<username>/feed/', views.feed, name="author_feed"),
    
    # Login
    path('oauth2_login/<provider>/', views.oauth2_login, name="oauth2_login"),
    path('oauth2callback/<provider>/', views.oauth2callback, name="oauth2callback"),
    path('logout/', views.logout, name='logout'),
    
    # Admin
    path('admin/one_time_elevation/', views.admin_one_time_elevation, name='admin_one_time_elevation'),
    path('admin/posts_overview/', views.admin_posts_overview, name='admin_posts_overview'),
    path('admin/pages_overview/', views.admin_pages_overview, name='admin_pages_overview'),
    path('admin/users_overview/', views.admin_users_overview, name='admin_users_overview'),
    path('admin/edit_post/', views.admin_edit_post, name='admin_edit_post'),
    path('admin/edit_page/', views.admin_edit_page, name='admin_edit_page'),
    path('admin/delete_file/<doc_type>/<pk>/<filename>/', views.admin_delete_file, name='admin_delete_file'),
    path('admin/backup_overview', views.admin_backup_overview, name='admin_backup_overview'),
    path('admin/backup', views.admin_backup, name='admin_backup'),
    path('admin/restore_backup', views.admin_restore_backup, name='admin_restore_backup'),
    
    # Pages
    path('<slug:uid>/', views.page, name="page"),
    path('<slug:uid>/<filename>/', views.page_file, name="page_file"),
]
