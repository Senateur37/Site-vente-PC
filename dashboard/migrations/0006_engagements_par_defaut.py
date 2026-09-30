from django.db import migrations

PAR_DEFAUT = [
    ("🚚", "Livraison rapide", "Partout, à votre porte"),
    ("💳", "Paiement à la livraison", "Sécurité garantie"),
    ("🛡️", "Produits garantis", "Qualité 100% vérifiée"),
]


def creer(apps, schema_editor):
    Engagement = apps.get_model("dashboard", "Engagement")
    if Engagement.objects.exists():
        return
    for ordre, (icone, titre, texte) in enumerate(PAR_DEFAUT):
        Engagement.objects.create(icone=icone, titre=titre, texte=texte, ordre=ordre)


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0005_contenu_du_site")]
    operations = [migrations.RunPython(creer, migrations.RunPython.noop)]
