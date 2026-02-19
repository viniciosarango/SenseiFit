from django.db import migrations, models
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_membership_courtesy_qty_membership_courtesy_used_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(
                fields=["client", "gym"],
                condition=Q(operational_status="ACTIVE"),
                name="uniq_active_membership_per_client_gym",
            ),
        ),
    ]
