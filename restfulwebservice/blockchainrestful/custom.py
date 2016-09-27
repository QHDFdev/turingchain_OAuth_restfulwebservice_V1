"""
Custom permissions define.
"""

from rest_framework.permissions import BasePermission
from rest_condition import ConditionalPermission, C, And, Or, Not


class IsTest(BasePermission):
    '''
    permissions for test
    '''
    def has_permission(self, request, view):
        return 'test' in [x['name'] for x in request.user.groups.values()]

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return 'admin' in [x['name'] for x in request.user.groups.values()]

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return 'user' in [x['name'] for x in request.user.groups.values()]

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return 'manager' in [x['name'] for x in request.user.groups.values()]
