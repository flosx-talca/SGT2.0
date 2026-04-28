# 🚀 SGT 2.0 — Sistema de Gestión de Turnos

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://www.postgresql.org/)

SGT 2.0 es una plataforma avanzada para la planificación y optimización de turnos laborales, diseñada para cumplir con las normativas legales vigentes y maximizar la eficiencia operativa.

---

## ✨ Características Principales

### ⚖️ Motor Legal Inteligente (SGT 2.1)
El corazón del sistema integra la **Ley 21.561** y normativas del Código del Trabajo:
- **Cálculo Automático de Horas**: Topes semanales (42h/44h) y diarios.
- **Semanas Cortas**: Prorrateo automático de horas para semanas de inicio y fin de mes.
- **Regla de Domingos**: Gestión de domingos libres obligatorios (Art. 38).
- **Estabilidad de Turno**: Algoritmo que favorece bloques continuos para mejorar la calidad de vida del trabajador.

### 🔒 Gestión Unificada de Disponibilidad
Sistema centralizado para manejar:
- **Ausencias**: Vacaciones, Licencias Médicas, Permisos.
- **Restricciones Técnicas**: Turnos fijos, exclusiones, turnos preferentes.
- **Prioridad Inteligente**: Las ausencias (vacaciones) tienen prioridad absoluta sobre cualquier restricción técnica.

### 🧠 Solver de Optimización
Utiliza **Google OR-Tools (CP-SAT)** para generar cuadrantes matemáticamente óptimos que equilibran:
1. Cobertura de dotación requerida.
2. Equidad en la carga de trabajo entre empleados.
3. Cumplimiento estricto de todas las reglas legales (Hard Constraints).
4. Preferencias y estabilidad (Soft Constraints).

---

## 🛠️ Instalación y Configuración

### Requisitos Previos
- Python 3.10 o superior.
- PostgreSQL en ejecución.
- Crear una base de datos llamada `sgt`.

### Instalación Rápida (Windows)
Ejecuta el script de configuración automática en PowerShell:
```powershell
./setup_project.ps1
```

### Instalación Rápida (Linux / macOS)
Ejecuta el script de configuración automática en la terminal:
```bash
chmod +x setup_project.sh
./setup_project.sh
```

Este script creará el entorno virtual, instalará dependencias, ejecutará migraciones y cargará los datos iniciales.

### Configuración Manual
1. Clonar el repositorio.
2. Crear entorno virtual: `python -m venv venv`.
3. Activar: 
   - Windows: `.\venv\Scripts\activate`
   - Linux: `source venv/bin/activate`
4. Instalar: `pip install -r requirements.txt`.
5. Configurar `.env` con tu `DATABASE_URL`.
6. Migrar: `flask db upgrade`.
7. Seeds: `python run_seed_reglas.py` e `python run_seed_parametros_legales.py`.

---

## 📖 Estructura del Proyecto

- `app/controllers/`: Blueprints y lógica de rutas.
- `app/models/`: Definición de tablas SQLAlchemy y Enums.
- `app/services/`: Motores de cálculo (`LegalEngine`) y utilidades.
- `app/scheduler/`: El "cerebro" del sistema (Builder del modelo CP-SAT).
- `app/templates/`: Vistas HTML modernas con CSS vanilla y HTMX.

---

## 📈 Próximos Pasos
- [ ] Integración con sistemas de marcado biométrico.
- [ ] Notificaciones push para trabajadores vía app móvil.
- [ ] Reportabilidad avanzada de costos laborales.

---
*Desarrollado con ❤️ por el equipo de Advanced Agentic Coding.*
