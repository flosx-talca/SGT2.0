# Guía de Configuración SGT 2.0 (Windows)

Sigue estos pasos en orden al descargar el proyecto o cambiar de servidor.

## 1. Ubicación
Abre una terminal (PowerShell o CMD) y asegúrate de estar en la raíz del proyecto:
`cd c:\Users\orozasi\Documents\GIT\SGT2.0\SGT2.0`

## 2. Crear Entorno Virtual (.venv)
Solo se hace la primera vez:
```powershell
python -m venv venv
```

## 3. Activar Entorno
**IMPORTANTE**: Debes hacer esto cada vez que abras una terminal nueva:
```powershell
.\venv\Scripts\activate
```

## 4. Instalar Dependencias
```powershell
pip install -r requirements.txt
```

## 5. Configurar Base de Datos (.env)
Usa el helper que creamos para no equivocarte con la clave:
```powershell
python setup_env.py
```

## 6. Preparar Base de Datos (Migraciones y Seed)
```powershell
# Sincronizar tablas
flask db upgrade

# Cargar datos iniciales (Turnos, Trabajadores)
python -m app.seed
```

## 7. Ejecutar Aplicación
```powershell
python run.py
```
La app estará disponible en `http://localhost:5000` y en tu red local.
