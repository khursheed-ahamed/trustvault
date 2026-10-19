from django.test import TestCase
from django.urls import reverse

from .models import User


class SignUpTests(TestCase):
    def test_signup_page_is_available_to_anonymous_users(self):
        response = self.client.get(reverse("accounts:signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an Account")

    def test_signup_creates_viewer_and_logs_user_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new_user",
                "password1": "SafePassword!734",
                "password2": "SafePassword!734",
            },
        )

        user = User.objects.get(username="new_user")
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(user.role, User.Role.VIEWER)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new_user",
                "password1": "SafePassword!734",
                "password2": "DifferentPassword!734",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="new_user").exists())
        self.assertIn("password2", response.context["form"].errors)
