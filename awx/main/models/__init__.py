# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.conf import settings # noqa

# AWX
from awx.main.models.base import * # noqa
from awx.main.models.unified_jobs import * # noqa
from awx.main.models.organization import * # noqa
from awx.main.models.credential import * # noqa
from awx.main.models.projects import * # noqa
from awx.main.models.inventory import * # noqa
from awx.main.models.jobs import * # noqa
from awx.main.models.events import * # noqa
from awx.main.models.ad_hoc_commands import * # noqa
from awx.main.models.schedules import * # noqa
from awx.main.models.activity_stream import * # noqa
from awx.main.models.ha import * # noqa
from awx.main.models.rbac import * # noqa
from awx.main.models.mixins import * # noqa
from awx.main.models.notifications import * # noqa
from awx.main.models.fact import * # noqa
from awx.main.models.label import * # noqa
from awx.main.models.workflow import * # noqa
from awx.main.models.channels import * # noqa
from awx.api.versioning import reverse
from awx.main.models.oauth import * # noqa
from oauth2_provider.models import Grant, RefreshToken # noqa -- needed django-oauth-toolkit model migrations



# Monkeypatch Django serializer to ignore django-taggit fields (which break
# the dumpdata command; see https://github.com/alex/django-taggit/issues/155).
from django.core.serializers.python import Serializer as _PythonSerializer
_original_handle_m2m_field = _PythonSerializer.handle_m2m_field


def _new_handle_m2m_field(self, obj, field):
    try:
        field.rel.through._meta
    except AttributeError:
        return
    return _original_handle_m2m_field(self, obj, field)


_PythonSerializer.handle_m2m_field = _new_handle_m2m_field


# Add custom methods to User model for permissions checks.
from django.contrib.auth.models import User  # noqa
from awx.main.access import * # noqa


User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)
User.add_to_class('can_access_with_errors', check_user_access_with_errors)
User.add_to_class('accessible_objects', user_accessible_objects)


@property
def user_get_organizations(user):
    return Organization.objects.filter(member_role__members=user)


@property
def user_get_admin_of_organizations(user):
    return Organization.objects.filter(admin_role__members=user)


@property
def user_get_auditor_of_organizations(user):
    return Organization.objects.filter(auditor_role__members=user)


User.add_to_class('organizations', user_get_organizations)
User.add_to_class('admin_of_organizations', user_get_admin_of_organizations)
User.add_to_class('auditor_of_organizations', user_get_auditor_of_organizations)


@property
def user_is_system_auditor(user):
    if not hasattr(user, '_is_system_auditor'):
        if user.pk:
            user._is_system_auditor = user.roles.filter(
                singleton_name='system_auditor', role_field='system_auditor').exists()
        else:
            # Odd case where user is unsaved, this should never be relied on
            return False
    return user._is_system_auditor


@user_is_system_auditor.setter
def user_is_system_auditor(user, tf):
    if user.id:
        if tf:
            Role.singleton('system_auditor').members.add(user)
            user._is_system_auditor = True
        else:
            Role.singleton('system_auditor').members.remove(user)
            user._is_system_auditor = False


User.add_to_class('is_system_auditor', user_is_system_auditor)


def user_is_in_enterprise_category(user, category):
    ret = (category,) in user.enterprise_auth.all().values_list('provider') and not user.has_usable_password()
    # NOTE: this if-else block ensures existing enterprise users are still able to
    # log in. Remove it in a future release
    if category == 'radius':
        ret = ret or not user.has_usable_password()
    elif category == 'saml':
        ret = ret or user.social_auth.all()
    return ret


User.add_to_class('is_in_enterprise_category', user_is_in_enterprise_category)




def o_auth2_application_get_absolute_url(self, request=None):
    return reverse('api:o_auth2_application_detail', kwargs={'pk': self.pk}, request=request)


OAuth2Application.add_to_class('get_absolute_url', o_auth2_application_get_absolute_url)


def o_auth2_token_get_absolute_url(self, request=None):
    return reverse('api:o_auth2_token_detail', kwargs={'pk': self.pk}, request=request)


OAuth2AccessToken.add_to_class('get_absolute_url', o_auth2_token_get_absolute_url)


# Import signal handlers only after models have been defined.
import awx.main.signals # noqa

from awx.main.registrar import activity_stream_registrar # noqa
activity_stream_registrar.connect(Organization)
activity_stream_registrar.connect(Inventory)
activity_stream_registrar.connect(Host)
activity_stream_registrar.connect(Group)
activity_stream_registrar.connect(InventorySource)
#activity_stream_registrar.connect(InventoryUpdate)
activity_stream_registrar.connect(Credential)
activity_stream_registrar.connect(CredentialType)
activity_stream_registrar.connect(Team)
activity_stream_registrar.connect(Project)
#activity_stream_registrar.connect(ProjectUpdate)
activity_stream_registrar.connect(JobTemplate)
activity_stream_registrar.connect(Job)
activity_stream_registrar.connect(AdHocCommand)
# activity_stream_registrar.connect(JobHostSummary)
# activity_stream_registrar.connect(JobEvent)
# activity_stream_registrar.connect(Profile)
activity_stream_registrar.connect(Schedule)
activity_stream_registrar.connect(CustomInventoryScript)
activity_stream_registrar.connect(NotificationTemplate)
activity_stream_registrar.connect(Notification)
activity_stream_registrar.connect(Label)
activity_stream_registrar.connect(User)
activity_stream_registrar.connect(WorkflowJobTemplate)
activity_stream_registrar.connect(WorkflowJobTemplateNode)
activity_stream_registrar.connect(WorkflowJob)
activity_stream_registrar.connect(OAuth2Application)
activity_stream_registrar.connect(OAuth2AccessToken)

# prevent API filtering on certain Django-supplied sensitive fields
prevent_search(User._meta.get_field('password'))
