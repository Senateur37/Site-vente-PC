from django.db import migrations

ROLES = ["Administrateur", "Gestionnaire de commandes", "Gestionnaire de catalogue"]


def creer(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nom in ROLES:
        Group.objects.get_or_create(name=nom)


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0007_journal_et_historique"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]
    operations = [migrations.RunPython(creer, migrations.RunPython.noop)]
