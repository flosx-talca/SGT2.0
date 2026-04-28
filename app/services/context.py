"""
Servicio central de contexto multiempresa.
Todas las queries filtradas por empresa pasan por aquí.
"""
from flask import session, abort
from flask_login import current_user

def get_empresa_activa_id():
    """
    Retorna empresa_id activo.
    Super Admin → session (puede ser None = ve todo)
    Cliente     → sus empresas via cliente_id
    Admin       → sus empresas via UsuarioEmpresa
    """
    if not current_user.is_authenticated:
        return None

    # Si ya está en sesión, lo usamos
    emp_id = session.get('empresa_activa_id')
    
    # Si no está en sesión pero el usuario tiene uno preferido en BD, lo usamos
    if not emp_id and hasattr(current_user, 'empresa_activa_id') and current_user.empresa_activa_id:
        emp_id = current_user.empresa_activa_id
        session['empresa_activa_id'] = emp_id

    # Validar acceso si no es Super Admin
    if emp_id and not current_user.is_super_admin:
        if not usuario_tiene_acceso(current_user, emp_id):
            session.pop('empresa_activa_id', None)
            return None

    return emp_id

def get_empresa_activa():
    """Retorna el objeto Empresa activa o None."""
    from app.models.business import Empresa
    empresa_id = get_empresa_activa_id()
    return Empresa.query.get(empresa_id) if empresa_id else None

def get_empresas_usuario():
    """Lista de empresas que puede ver el usuario actual."""
    from app.models.business import Empresa
    from app.models.auth import UsuarioEmpresa

    if not current_user.is_authenticated:
        return []

    if current_user.is_super_admin:
        return Empresa.query.filter_by(activo=True)\
                            .order_by(Empresa.razon_social).all()

    if current_user.is_cliente:
        return Empresa.query.filter_by(
            cliente_id=current_user.cliente_id, activo=True
        ).order_by(Empresa.razon_social).all()

    # Administrador (Rol normal)
    ids = [ue.empresa_id for ue in current_user.empresas if ue.activo]
    if not ids:
        return []
    return Empresa.query.filter(
        Empresa.id.in_(ids), Empresa.activo == True
    ).order_by(Empresa.razon_social).all()

def usuario_tiene_acceso(usuario, empresa_id):
    """Verifica si el usuario puede acceder a una empresa."""
    from app.models.business import Empresa
    from app.models.auth import UsuarioEmpresa

    if usuario.is_super_admin:
        return True

    if usuario.is_cliente:
        empresa = Empresa.query.get(empresa_id)
        return empresa and empresa.cliente_id == usuario.cliente_id

    return UsuarioEmpresa.query.filter_by(
        usuario_id=usuario.id,
        empresa_id=empresa_id,
        activo=True
    ).first() is not None
