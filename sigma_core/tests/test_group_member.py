import json

from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase

from sigma_core.models.user import User
from sigma_core.models.group import Group
from sigma_core.models.group_member import GroupMember
from sigma_core.serializers.user import DetailedUserSerializer as UserSerializer
from sigma_core.tests.factories import UserFactory, AdminUserFactory, GroupFactory, GroupMemberFactory

# Test /rank, /kick
class GroupMemberPermissionTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.member_rank_url = "/group-member/%d/rank/"
        self.member_url = "/group-member/%d/"
        self.users = UserFactory.create_batch(6)
        self.group = GroupFactory(req_rank_promote=3, req_rank_demote=4, req_rank_kick=5)
        self.mships = [
            None,
            GroupMemberFactory(user=self.users[1], group=self.group, perm_rank=1),
            GroupMemberFactory(user=self.users[2], group=self.group, perm_rank=2),
            GroupMemberFactory(user=self.users[3], group=self.group, perm_rank=3),
            GroupMemberFactory(user=self.users[4], group=self.group, perm_rank=4),
            GroupMemberFactory(user=self.users[5], group=self.group, perm_rank=5)
        ]

    def try_rank(self, userId, targetId, newPermRank, expectedHttpResponseCode):
        """
        This function attempts to set $targetId membership rank to $newPermRank
        using $userId permissions
        PUT /group-member/{targetId}/rank with perm_rank=newPermRank
        """
        if userId >= 0:
            self.client.force_authenticate(user=self.users[userId])
        response = self.client.put(self.member_rank_url % (self.mships[targetId].id), {"perm_rank": newPermRank})
        self.assertEqual(response.status_code, expectedHttpResponseCode)

    def try_delete(self, userId, targetId, expectedHttpResponseCode):
        """
        This function attempts to remove $targetId membership from Group
        using $userId permissions
        DELETE /group-member/{targetId}/
        """
        if userId >= 0:
            self.client.force_authenticate(user=self.users[userId])
        response = self.client.delete(self.member_url % targetId)
        self.assertEqual(response.status_code, expectedHttpResponseCode)

    # /rank
    def test_rank_not_authed(self):
        self.try_rank(-1, 1, 4, status.HTTP_401_UNAUTHORIZED)

    def test_rank_not_group_member(self):
        self.try_rank(0, 1, 4, status.HTTP_404_NOT_FOUND)

    def test_rank_demote_no_permission(self):
        self.try_rank(1, 2, 1, status.HTTP_403_FORBIDDEN)

    def test_rank_demote_no_permission2(self):
        self.try_rank(3, 2, 1, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GroupMember.objects.get(pk=self.mships[2].id).perm_rank, 2)

    def test_rank_promote_no_permission(self):
        self.try_rank(1, 1, 2, status.HTTP_403_FORBIDDEN)

    def test_rank_no_rank_change(self):
        self.try_rank(5, 1, 1, status.HTTP_400_BAD_REQUEST)

    def test_rank_not_a_number(self):
        self.try_rank(5, 1, "hi!", status.HTTP_400_BAD_REQUEST)

    def test_rank_set_rank_to_zero(self):
        self.try_rank(5, 1, 0, status.HTTP_400_BAD_REQUEST)

    def test_rank_bad_rank(self):
        self.try_rank(5, 1, -1, status.HTTP_400_BAD_REQUEST)
        self.try_rank(5, 1, Group.ADMINISTRATOR_RANK + 1, status.HTTP_400_BAD_REQUEST)

    def test_rank_too_high_rank(self):
        self.try_rank(5, 1, 5, status.HTTP_403_FORBIDDEN)

    def test_rank_promote_ok(self):
        self.try_rank(3, 1, 2, status.HTTP_200_OK)
        self.assertEqual(GroupMember.objects.get(pk=self.mships[1].id).perm_rank, 2)

    def test_rank_demote_ok(self):
        self.try_rank(5, 3, 2, status.HTTP_200_OK)
        self.assertEqual(GroupMember.objects.get(pk=self.mships[3].id).perm_rank, 2)

    def test_rank_demote_self_ok(self):
        self.try_rank(3, 3, 2, status.HTTP_200_OK)
        self.assertEqual(GroupMember.objects.get(pk=self.mships[3].id).perm_rank, 2)

    # delete
    def test_delete_not_authed(self):
        self.try_delete(-1, 1, status.HTTP_401_UNAUTHORIZED)

    def test_delete_not_group_member(self):
        self.try_delete(0, 1, status.HTTP_404_NOT_FOUND)

    def test_delete_no_permission(self):
        self.try_delete(3, 2, status.HTTP_403_FORBIDDEN)

    def test_delete_user_not_in_group(self):
        self.try_delete(4, 0, status.HTTP_404_NOT_FOUND)

    def test_delete_self_ok(self):
        self.try_delete(1, 1, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GroupMember.objects.filter(pk=self.mships[1].id).exists())

    def test_delete_ok(self):
        self.try_delete(5, 1, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GroupMember.objects.filter(pk=self.mships[1].id).exists())

class OpenGroupMemberCreationTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(APITestCase, self).setUpTestData()

        # Routes
        self.members_url = "/group-member/"
        self.member_url = self.members_url + "%d/"

        # Group open to anyone
        self.group = GroupFactory()
        self.group.default_member_rank = 1
        self.group.save()

        # Users already in group
        self.users = [UserFactory()]
        # Associated GroupMember
        self.group_member1 = GroupMember(user=self.users[0], group=self.group, perm_rank=Group.ADMINISTRATOR_RANK)

        # Testing user
        self.user = UserFactory()

        # Misc
        self.new_membership_data = {"group": self.group.id, "user": self.user.id}

    def test_create_not_authed(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_not_for_self(self):
        # Attempt to add somebody else to a group
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_success(self):
        # Succesful attempt to join an open group
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['perm_rank'], self.group.default_member_rank)


class RequestGroupMemberCreationTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(APITestCase, self).setUpTestData()

        # Routes
        self.members_url = "/group-member/"
        self.accept_join_requests_url = self.members_url + "%d/accept_join_request/"

        # Group with membership request
        self.group = GroupFactory(default_member_rank=0, req_rank_accept_join_requests=5)

        # Users already in group
        self.users = UserFactory.create_batch(3)
        # Associated GroupMember
        self.group_member1 = GroupMemberFactory(user=self.users[0], group=self.group, perm_rank=Group.ADMINISTRATOR_RANK) # can validate requests
        self.group_member2 = GroupMemberFactory(user=self.users[1], group=self.group, perm_rank=1) # cannot validate requests
        self.group_member3 = GroupMemberFactory(user=self.users[2], group=self.group, perm_rank=0) # request to be validated

        # Testing user
        self.user = UserFactory()

        # Misc
        self.new_membership_data = {"group": self.group.id, "user": self.user.id}

    def test_create_not_authed(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_success(self):
        # Succesful attempt to request group membership
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['perm_rank'], self.group.default_member_rank)

    def test_validate_forbidden(self):
        # Attempt to validate a request but not enough permission
        self.client.force_authenticate(user=self.users[1])
        response = self.client.put(self.accept_join_requests_url % self.group_member3.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validate_success(self):
        # Succesful attempt to validate a request
        self.client.force_authenticate(user=self.users[0])
        response = self.client.put(self.accept_join_requests_url % self.group_member3.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['perm_rank'], 1)


class InvitationGroupMemberCreationTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(APITestCase, self).setUpTestData()

        # Routes
        self.members_url = "/group-member/"

        # Group with invitation only
        self.group = GroupFactory(req_rank_invite=5, default_member_rank=-1, visibility=Group.VIS_PRIVATE)

        # Testing user
        self.users = UserFactory.create_batch(2)
        self.memberships = [
            None,
            GroupMemberFactory(user=self.users[1], group=self.group, perm_rank=self.group.req_rank_invite)
        ]

        # Misc
        self.new_membership_data = {"group": self.group.id, "user": self.users[0].id}

    def test_create_not_authed(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_forbidden(self):
        # Can't join this Group
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_already_group_member(self):
        self.client.force_authenticate(user=self.users[1])
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_self_forbidden(self):
        self.client.force_authenticate(user=self.users[1])
        response = self.client.post(self.members_url, self.new_membership_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationGroupMemberInvitationWorkflowTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        super(APITestCase, self).setUpTestData()

        # Routes
        self.members_url = "/group-member/"
        self.group_invite_url = "/group/%d/invite/";
        self.group_invite_accept_url = "/group/%d/invite_accept/";

        # Group with invitation only
        self.group = GroupFactory(req_rank_invite=5, default_member_rank=-1)

        # Testing user
        self.users = UserFactory.create_batch(2)
        self.memberships = [
            None,
            GroupMemberFactory(user=self.users[1], group=self.group, perm_rank=self.group.req_rank_invite)
        ]

    def test_invite_not_authed(self):
        self.client.force_authenticate(user=None)
        response = self.client.put(self.group_invite_url % (self.group.id), {"user": self.users[0].id} )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invite_forbidden(self):
        # Attempt to get group membership
        self.client.force_authenticate(user=self.users[0])
        response = self.client.put(self.group_invite_url % (self.group.id), {"user": self.users[0].id} )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invite_already_group_member(self):
        # Attempt to get group membership
        self.client.force_authenticate(user=self.users[1])
        response = self.client.put(self.group_invite_url % (self.group.id), {"user": self.users[1].id} )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_ok(self):
        # User0 invites User1 to group
        self.client.force_authenticate(user=self.users[1])
        response = self.client.put(self.group_invite_url % (self.group.id), {"user": self.users[0].id} )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invite_accept(self):
        self.test_invite_ok()
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(self.members_url, {"user": self.users[0].id, "group": self.group.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
