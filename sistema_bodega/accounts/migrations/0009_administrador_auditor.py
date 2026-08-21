from django.db import migrations


def crear_administrador_auditor(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type, _ = ContentType.objects.get_or_create(
        app_label='accounts',
        model='customuser',
    )
    permission_specs = [
        ('can_access_admin', 'Acceso al panel de administración'),
        ('can_manage_users', 'Gestión de usuarios'),
        ('can_manage_departments', 'Gestión de departamentos'),
        ('can_edit', 'Edición de registros'),
    ]
    permissions = {}
    for codename, name in permission_specs:
        perm, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={'name': name},
        )
        permissions[codename] = perm

    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    admin_auditor_group, _ = Group.objects.get_or_create(name='Administrador Auditor')

    admin_group.permissions.set([
        permissions['can_manage_users'],
        permissions['can_manage_departments'],
        permissions['can_edit'],
    ])

    perms_accounts = list(
        Permission.objects.filter(content_type__app_label='accounts')
    )
    admin_auditor_group.permissions.set(perms_accounts)


def quitar_administrador_auditor(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    content_type = ContentType.objects.filter(app_label='accounts', model='customuser').first()
    if content_type:
        perms = {
            p.codename: p
            for p in Permission.objects.filter(
                content_type=content_type,
                codename__in=[
                    'can_access_admin',
                    'can_manage_users',
                    'can_manage_departments',
                    'can_edit',
                ],
            )
        }
        admin_group = Group.objects.filter(name='Administrador').first()
        if admin_group and perms:
            admin_group.permissions.set([
                perms[c] for c in perms
            ])
    Group.objects.filter(name='Administrador Auditor').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_transaccion_lote'),
    ]

    operations = [
        migrations.RunPython(crear_administrador_auditor, quitar_administrador_auditor),
    ]
