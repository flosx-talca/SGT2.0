import json
from flask import jsonify, make_response

def htmx_error(message, status_code=400, type="error"):
    """
    Retorna una respuesta JSON de error con headers de HTMX 
    para disparar un ToastR en el frontend.
    """
    response = jsonify({'ok': False, 'msg': message})
    
    # Header HX-Trigger para que JS lo capture
    # Formato: {"nombreEvento": {"param": "valor"}}
    trigger_data = {
        "mostrarToast": {
            "msg": message,
            "type": type
        }
    }
    
    response.headers['HX-Trigger'] = json.dumps(trigger_data)
    return response, status_code
