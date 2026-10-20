from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Creates or updates demo accounts: admin_demo, owner_demo, and viewer_demo."

    def handle(self, *args, **options):
        demo_users = [
            {
                "username": "admin_demo",
                "email": "admin@trustvault.local",
                "password": "DemoPassword123!",
                "role": User.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "owner_demo",
                "email": "owner@trustvault.local",
                "password": "DemoPassword123!",
                "role": User.OWNER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "viewer_demo",
                "email": "viewer@trustvault.local",
                "password": "DemoPassword123!",
                "role": User.VIEWER,
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for user_data in demo_users:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "role": user_data["role"],
                    "is_staff": user_data["is_staff"],
                    "is_superuser": user_data["is_superuser"],
                },
            )

            # Ensure all required attributes are updated if user already existed
            if not created:
                user.email = user_data["email"]
                user.role = user_data["role"]
                user.is_staff = user_data["is_staff"]
                user.is_superuser = user_data["is_superuser"]

            user.set_password(user_data["password"])
            user.save()

            action_label = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{action_label}] {user.username} (Role: {user.role}, Staff: {user.is_staff}, Superuser: {user.is_superuser})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("\nSuccessfully set up all demo users!")
        )
