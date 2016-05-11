import json

from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate

from sigma_core.tests.factories import UserFactory, AdminUserFactory, GroupMemberFactory, GroupFactory, ClusterFactory
from sigma_core.serializers.user import MinimalUserSerializer, UserSerializer, MyUserSerializer
from sigma_core.models.group import Group
from sigma_core.models.group_member import GroupMember

class UserTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        # Summary: 2 clusters, 2 groups, 10 users
        # Cluster #1: users #1 to #5
        # Cluster #2: users #5 to #9
        # Group #1: users #1, #2 and #6 (pending request)
        # Group #2: users #3, #7 and #8 (invitation not accepted yet)
        # User #1 is admin in cluster #1
        # User #6 is admin in cluster #2
        # User #10 is Sigma admin

        super(UserTests, self).setUpTestData()
        self.clusters = ClusterFactory.create_batch(2)
        self.users = UserFactory.create_batch(9)
        self.groups = GroupFactory.create_batch(2)

        # User #10 is Sigma admin
        self.users.append(AdminUserFactory())

        # Add users in clusters (user #1 is admin in cluster #1 and user #6 is admin in cluster #2)
        for i in range(5):
            self.clusters[0].cluster_users.add(self.users[i])
            GroupMemberFactory(group=self.clusters[0], user=self.users[i], perm_rank=(Group.ADMINISTRATOR_RANK if i == 0 else 1))

            self.clusters[1].cluster_users.add(self.users[4+i])
            GroupMemberFactory(group=self.clusters[1], user=self.users[4+i], perm_rank=(Group.ADMINISTRATOR_RANK if i == 1 else 1))

        # Add users in group #1
        GroupMemberFactory(group=self.groups[0], user=self.users[0], perm_rank=1)
        GroupMemberFactory(group=self.groups[0], user=self.users[1], perm_rank=1)
        GroupMemberFactory(group=self.groups[0], user=self.users[5], perm_rank=0) # pending request

        # Add users in group #2
        GroupMemberFactory(group=self.groups[1], user=self.users[2], perm_rank=1)
        GroupMemberFactory(group=self.groups[1], user=self.users[6], perm_rank=1)
        self.users[7].invited_to_groups.add(self.groups[1]) # User #8 is invited to group #2

        self.user_url = '/user/'
        self.new_user_data = {'lastname': 'Doe', 'firstname': 'John', 'email': 'john.doe@newschool.edu', 'password': 'password', 'clusters_ids' : {self.clusters[0].id}}

#### List requests
    def test_get_users_list_unauthed(self):
        # Client not authenticated
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_users_list_user1(self):
        # Client authenticated: user in cluster #1, can see users in cluster #1 and in his groups
        self.client.force_authenticate(user=self.users[0])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)

    def test_get_users_list_user4(self):
        # Client authenticated: user in cluster #1, can see users in cluster #1
        self.client.force_authenticate(user=self.users[3])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_users_list_user5(self):
        # Client authenticated: user in clusters #1 and #2, can see eveybody (except admin user) then
        self.client.force_authenticate(user=self.users[4])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

    def test_get_users_list_user6(self):
        # Client authenticated: user in cluster #2, pending request to group #2 (cannot see members yet)
        self.client.force_authenticate(user=self.users[5])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_users_list_user8(self):
        # Client authenticated: user in cluster #2, invited to group #2 (cannot see members yet)
        self.client.force_authenticate(user=self.users[7])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_get_users_list_admin_user(self):
        # Client authenticated: Sigma admin, can see everyone
        self.client.force_authenticate(user=self.users[9])
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

#### Get requests
    def test_get_user_unauthed(self):
        # Client is not authenticated
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_1_req_5(self):
        # Client authenticated: request user in same cluster
        self.client.force_authenticate(user=self.users[0])
        response = self.client.get(self.user_url + "%d/" % self.users[4].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[4].lastname)
        self.assertEqual(response.data['email'], self.users[4].email)
        self.assertEqual(response.data['clusters_ids'], [c.id for c in self.clusters])

    def test_get_user_3_req_7(self):
        # Client authenticated: request user in same group
        self.client.force_authenticate(user=self.users[2])
        response = self.client.get(self.user_url + "%d/" % self.users[6].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[6].lastname)
        self.assertEqual(response.data['email'], self.users[6].email)
        self.assertEqual(response.data['clusters_ids'], [self.clusters[1].id])

    def test_get_user_1_req_7(self):
        # Client authenticated: no group in common
        self.client.force_authenticate(user=self.users[0])
        response = self.client.get(self.user_url + "%d/" % self.users[6].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[6].lastname)
        self.assertEqual(response.data['clusters_ids'], [self.clusters[1].id])
        self.assertNotIn('email', response.data)
        self.assertNotIn('photo', response.data)

    def test_get_user_2_req_6(self):
        # Client authenticated: request user who has pending request into group
        self.client.force_authenticate(user=self.users[1])
        response = self.client.get(self.user_url + "%d/" % self.users[5].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[5].lastname)
        self.assertEqual(response.data['clusters_ids'], [self.clusters[1].id])
        self.assertIn('email', response.data)

    def test_get_user_8_req_3(self):
        # Client authenticated: request a user who is in a group I'm invited
        self.client.force_authenticate(user=self.users[7])
        response = self.client.get(self.user_url + "%d/" % self.users[2].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[2].lastname)
        self.assertEqual(response.data['clusters_ids'], [self.clusters[0].id])
        self.assertNotIn('email', response.data)
        self.assertNotIn('photo', response.data)

    def test_get_user_3_req_8(self):
        # Client authenticated: request a user who is invited in a group whose I'm a member
        self.client.force_authenticate(user=self.users[2])
        response = self.client.get(self.user_url + "%d/" % self.users[7].id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], self.users[7].lastname)
        self.assertEqual(response.data['clusters_ids'], [self.clusters[1].id])
        self.assertNotIn('email', response.data)
        self.assertNotIn('photo', response.data)


#### "Get my data" requests
    def test_get_my_data_unauthed(self):
        # Client is not authenticated
        response = self.client.get(self.user_url + 'me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_my_data_ok(self):
        # Client is authenticated
        self.client.force_authenticate(user=self.users[1])
        response = self.client.get(self.user_url + 'me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.users[1].id)
        self.assertIn('invited_to_groups_ids', response.data)

#### Create requests
    def test_create_user_unauthed(self):
        # Client is not authenticated
        response = self.client.post(self.user_url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_user_not_cluster_admin(self):
        # Client has no permission
        self.client.force_authenticate(user=self.users[1])
        response = self.client.post(self.user_url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_sigma_admin_ok(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[9])
        response = self.client.post(self.user_url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['lastname'], self.new_user_data['lastname'])
        self.assertTrue(GroupMember.objects.filter(user=response.data['id'], group=self.clusters[0].id).exists())

    def test_create_user_admin__bad_request1(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[9])
        data = self.new_user_data.copy()
        data['clusters_ids'] = 'Completely wrong'
        response = self.client.post(self.user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_admin__bad_request2(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[9])
        data = self.new_user_data.copy()
        data['clusters_ids'] = {'cluster': 1}
        response = self.client.post(self.user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_admin__bad_request3(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[9])
        data = self.new_user_data.copy()
        data['clusters_ids'] = None
        response = self.client.post(self.user_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_clusteradmin_ok(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post(self.user_url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['lastname'], self.new_user_data['lastname'])
        self.assertTrue(GroupMember.objects.filter(user=response.data['id'], group=self.clusters[0].id).exists())

    def test_create_user_clusteradmin_wrong_cluster(self):
        # Client has permissions
        self.client.force_authenticate(user=self.users[4])
        response = self.client.post(self.user_url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#### Modification requests
    def test_edit_email_wrong_permission(self):
        # Client wants to change another user's email
        self.client.force_authenticate(user=self.users[1])
        user_data = UserSerializer(self.users[0]).data
        user_data['email'] = "pi@random.org"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_is_superuser_no_permission(self):
        # Client can't set himself as administrator !
        self.client.force_authenticate(user=self.users[1])
        user_data = UserSerializer(self.users[1]).data
        user_data['is_superuser'] = True
        response = self.client.put(self.user_url + "%d/" % self.users[1].id, user_data)
        self.assertFalse(self.users[1].is_superuser)

    def test_edit_email_nonvalid_email(self):
        # Client wants to change his email with a non valid value
        self.client.force_authenticate(user=self.users[0])
        user_data = UserSerializer(self.users[0]).data
        user_data['email'] = "ThisIsNotAnEmail"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_email_ok(self):
        # Client wants to change his email and succeed in
        self.client.force_authenticate(user=self.users[1])
        user_data = UserSerializer(self.users[1]).data
        old_email = user_data['email']
        user_data['email'] = "pi@random.org"
        response = self.client.put(self.user_url + "%d/" % self.users[1].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user_data['email'])
        # Guarantee that tests are independant
        self.users[1].email = old_email
        self.users[1].save()

    def test_edit_profile_wrong_permission(self):
        # Client wants to change another user's phone number
        self.client.force_authenticate(user=self.users[1])
        user_data = UserSerializer(self.users[0]).data
        user_data['phone'] = "0123456789"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_profile_ok(self):
        # Client wants to change his phone number
        self.client.force_authenticate(user=self.users[0])
        user_data = UserSerializer(self.users[0]).data
        old_phone = user_data['phone']
        user_data['phone'] = "0123456789"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], user_data['phone'])
        # Guarantee that tests are independant
        self.users[0].phone = old_phone
        self.users[0].save()

    def test_edit_lastname_oneself(self):
        # Client wants to change his lastname
        self.client.force_authenticate(user=self.users[1])
        user_data = UserSerializer(self.users[1]).data
        user_data['lastname'] = "Daudet"
        response = self.client.put(self.user_url + "%d/" % self.users[1].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_lastname_oneself_clusteradmin(self):
        # Client wants to change his lastname
        self.client.force_authenticate(user=self.users[0])
        user_data = UserSerializer(self.users[0]).data
        old_lastname = user_data['lastname']
        user_data['lastname'] = "Daudet"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], user_data['lastname'])
        # Guarantee that tests are independant
        self.users[1].lastname = old_lastname
        self.users[1].save()

    def test_edit_lastname_cluster_admin(self):
        # Cluster admin wants to change the lastname of one cluster's member
        self.client.force_authenticate(user=self.users[0])
        user_data = UserSerializer(self.users[1]).data
        old_lastname = user_data['lastname']
        user_data['lastname'] = "Daudet"
        response = self.client.put(self.user_url + "%d/" % self.users[1].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], user_data['lastname'])
        # Guarantee that tests are independant
        self.users[0].lastname = old_lastname
        self.users[0].save()

    def test_edit_lastname_sigma_admin(self):
        # Admin wants to change an user's lastname
        self.client.force_authenticate(user=self.users[9])
        user_data = UserSerializer(self.users[0]).data
        old_lastname = user_data['lastname']
        user_data['lastname'] = "Daudet"
        response = self.client.put(self.user_url + "%d/" % self.users[0].id, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lastname'], user_data['lastname'])
        # Guarantee that tests are independant
        self.users[0].lastname = old_lastname
        self.users[0].save()

#### "Change password" requests
    def test_change_pwd_wrong_pwd(self):
        # Client gives a wrong old password
        self.users[0].set_password('old_pwd')
        self.client.force_authenticate(user=self.users[0])
        response = self.client.put(self.user_url + 'change_password/', {'old_password': 'wrong', 'password': 'new_pwd'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_pwd_no_pwd(self):
        # Client gives no new password
        self.users[0].set_password('old_pwd')
        self.client.force_authenticate(user=self.users[0])
        response = self.client.put(self.user_url + 'change_password/', {'old_password': 'old_pwd', 'password': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_pwd_ok(self):
        # Client successfully changes his password
        self.users[0].set_password('old_pwd')
        self.client.force_authenticate(user=self.users[0])
        response = self.client.put(self.user_url + 'change_password/', {'old_password': 'old_pwd', 'password': 'new_strong_pwd'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

#### "Reset password" requests
    def test_reset_pwd_no_email(self):
        # Client gives no email
        response = self.client.post(self.user_url + 'reset_password/', {'email': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_pwd_no_user(self):
        # Client's email is not found
        response = self.client.post(self.user_url + 'reset_password/', {'email': 'unknown@email.me'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_pwd_ok(self):
        # Client successfully resets his password
        response = self.client.post(self.user_url + 'reset_password/', {'email': self.users[0].email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        from sigma_core.views.user import reset_mail
        self.assertEqual(mail.outbox[0].subject, reset_mail['subject'])

#### "Add photo" requests
    def test_addphoto_ok(self):
        self.client.force_authenticate(user=self.users[0])
        with open("sigma_files/test_img.png", "rb") as img:
            response = self.client.post(self.user_url + "addphoto/", {'file': img}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

# #### Deletion requests
