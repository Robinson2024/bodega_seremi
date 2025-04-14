from django.db import migrations
from django.contrib.auth.models import Group, Permission

def create_groups(apps, schema_editor):
    # Crear grupos
    admin_group, _ = Group.objects.get_or_create(name='Administrador')
    bodega_group, _ = Group.objects.get_or_create(name='Usuario de Bodega')
    auditor_group, _ = Group.objects.get_or_create(name='Auditor')

    # Obtener permisos
    can_access_admin = Permission.objects.get(codename='can_access_admin')
    can_manage_users = Permission.objects.get(codename='can_manage_users')
    can_manage_departments = Permission.objects.get(codename='can_manage_departments')
    can_edit = Permission.objects.get(codename='can_edit')

    # Asignar permisos a Administrador (todos los permisos)
    admin_group.permissions.set([
        can_access_admin,
        can_manage_users,
        can_manage_departments,
        can_edit,
    ])

    # Asignar permisos a Usuario de Bodega (todos excepto gestión de usuarios y departamentos)
    bodega_group.permissions.set([
        can_edit,
    ])

    # Asignar permisos a Auditor (sin permisos de edición)
    auditor_group.permissions.set([])

def remove_groups(apps, schema_editor):
    Group.objects.filter(name__in=['Administrador', 'Usuario de Bodega', 'Auditor']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]