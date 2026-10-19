"""Management command to create three sample user accounts."""
from django.core.management.base import BaseCommand

from accounts.models import User


SEED_USERS = [
    {"username": "alice_admin", "password": "TrustVault1!", "role": User.Role.ADMIN},
    {"username": "bob_owner", "password": "TrustVault2!", "role": User.Role.OWNER},
    {"username": "carol_viewer", "password": "TrustVault3!", "role": User.Role.VIEWER},
]


class Command(BaseCommand):
    help = "Create sample admin, owner, and viewer accounts."

    def handle(self, *args, **options):
        for data in SEED_USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"role": data["role"]},
            )
            if created:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Created {data['role']} user: {data['username']}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"User already exists: {data['username']}"
                ))
