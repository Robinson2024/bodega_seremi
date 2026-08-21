from django.db import migrations


def create_groups(apps, schema_editor):
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
    bodega_group, _ = Group.objects.get_or_create(name='Usuario de Bodega')
    auditor_group, _ = Group.objects.get_or_create(name='Auditor')

    admin_group.permissions.set([
        permissions['can_access_admin'],
        permissions['can_manage_users'],
        permissions['can_manage_departments'],
        permissions['can_edit'],
    ])
    bodega_group.permissions.set([
        permissions['can_edit'],
    ])
    auditor_group.permissions.set([])


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Administrador', 'Usuario de Bodega', 'Auditor']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
