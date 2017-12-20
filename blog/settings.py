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

from django.conf import settings as project_settings

POSTS_PER_PAGE = int(project_settings.CONFIG["Blog"]["posts_per_page"])
ATOM_POSTS = int(project_settings.CONFIG["Blog"]["atom_posts"])

ONE_TIME_ADMIN_PASSWORD = project_settings.CONFIG["Secrets"]["one_time_admin_password"]

GOOGLE_OAUTH2_CLIENT_ID = project_settings.CONFIG["Secrets"]["google_oauth2_client_id"]
GOOGLE_OAUTH2_CLIENT_SECRET = project_settings.CONFIG["Secrets"]["google_oauth2_client_secret"]

GITHUB_OAUTH2_CLIENT_ID = project_settings.CONFIG["Secrets"]["github_oauth2_client_id"]
GITHUB_OAUTH2_CLIENT_SECRET = project_settings.CONFIG["Secrets"]["github_oauth2_client_secret"]
