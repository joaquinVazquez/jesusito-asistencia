import os

def configurar_entorno():
    """Genera la arquitectura de carpetas y el archivo de diseño central."""
    # 1. Definición de la arquitectura semántica
    directorios = [
        "src",                  # Código fuente
        "src/views",            # [UX/UI] Vistas
        "src/controllers",      # [Lógica] Orquestadores
        "src/models",           # [Datos] Base de datos
        "src/utils",            # [Soporte] Utilerías
        "assets",               # [UX] Recursos gráficos
        "config",               # [IA] Configuración global
        "data",                 # Base de datos física
        "logs",                 # Registro de errores
        "backups/local",        # Respaldos técnicos
        "backups/reports_pdf"   # Respaldos operativos
    ]
    
    for directorio in directorios:
        os.makedirs(directorio, exist_ok=True)
        print(f"Directorio listo: {directorio}/")

    # 2. Inyección de la paleta de colores corporativa
    theme_path = os.path.join("config", "theme.py")
    theme_content = """# Paleta de Colores - Jesusito Pastelerías
COLOR_PRIMARIO = "#560116"       # Vino oscuro
COLOR_SECUNDARIO = "#5C0318"     # Rojo borgoña
COLOR_ACENTO = "#823522"         # Terracota
COLOR_TEXTO_DESTACADO = "#DCA864" # Dorado
COLOR_FONDO = "#F6EFEB"          # Crema
"""
    with open(theme_path, "w", encoding="utf-8") as f:
        f.write(theme_content)
    
    print(f"\nArchivo de configuración visual creado en: {theme_path}")

if __name__ == "__main__":
    configurar_entorno()