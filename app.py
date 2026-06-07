import streamlit as st
import datetime
from src.models.db_manager import ejecutar_query, inicializar_pool
import pandas as pd
from fpdf import FPDF
import io

# 1. CONFIGURACIÓN BASE DE LA PÁGINA (Debe ser la primera instrucción)
st.set_page_config(page_title="Jesusito ERP V3", page_icon="🍰", layout="wide")

# 2. INICIALIZACIÓN DEL POOL DE CONEXIONES (Caché global)
@st.cache_resource
def init_db():
    """Mantiene la conexión abierta en el servidor web de forma eficiente"""
    inicializar_pool()
    return True

init_db()

# 3. GESTIÓN DE ESTADO (MEMORIA DE SESIÓN)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
    st.session_state.nombre_usuario = None

# 4. COMPONENTE DE LOGIN
def mostrar_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acceso al Sistema")
        st.markdown("---")
        pin = st.text_input("Ingrese su PIN de Acceso:", type="password")
        
        if st.button("Desbloquear", use_container_width=True):
            # Lógica de validación (MVP: PIN Maestro)
            # Próximamente lo conectaremos a la tabla de empleados para validar pines individuales
            res = ejecutar_query("SELECT valor FROM config WHERE parametro = 'pin_admin'", fetch=True)
            pin_real = res[0]['valor'] if res else "1234"
            
            if pin == pin_real:
                st.session_state.autenticado = True
                st.session_state.rol = "Admin"
                st.session_state.nombre_usuario = "Administrador Principal"
                st.rerun() # Fuerza la recarga de la página
            else:
                st.error("PIN Incorrecto. Acceso denegado.")

# 5. ESTRUCTURA PRINCIPAL (RBAC)
def mostrar_app():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.image("assets/logo_jesusito.png", use_container_width=True)
        st.write(f"👤 **{st.session_state.nombre_usuario}**")
        st.caption(f"Rol: {st.session_state.rol}")
        st.markdown("---")
        
        # Opciones dinámicas basadas en el rol
        menu = ["⏱️ Reloj Checador"]
        
        if st.session_state.rol in ['Admin', 'Encargado']:
            menu.append("📝 Registrar Encargos")
            
        if st.session_state.rol == 'Admin':
            menu.extend(["👥 Personal", "💰 Nómina", "⚙️ Permisos y Metas"])
            
        seleccion = st.radio("Navegación", menu)
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

    # --- ENRUTADOR DE VISTAS ---
    if seleccion == "⏱️ Reloj Checador":
        st.title("⏱️ Registro de Asistencia")
        st.markdown("Selecciona tu ubicación y marca tu entrada o salida. El sistema registra la hora exacta del servidor en la nube.")

        # 1. Cargar Sucursales
        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True) or []
        
        if not sucursales:
            st.error("No hay sucursales configuradas en el sistema.")
        else:
            mapa_suc = {s['nombre']: s['id'] for s in sucursales}
            
            # Contenedor principal de la interfaz
            with st.container(border=True):
                # 2. Selector de Sucursal
                suc_sel = st.selectbox("📍 Ubicación de la Terminal", list(mapa_suc.keys()))
                suc_id = mapa_suc[suc_sel]

                # 3. Lógica de Rotación (El Toggle de Excepción)
                st.markdown("<br>", unsafe_allow_html=True)
                modo_rotacion = st.toggle("🔄 Personal en rotación (Mostrar plantilla completa)", value=False, help="Activa esto si estás cubriendo turno en una sucursal que no es la tuya.")

                # 4. Consulta Dinámica de Empleados
                if modo_rotacion:
                    # Trae a todos los activos
                    query_emp = "SELECT id, nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre"
                    parametros = None
                else:
                    # Filtra solo a los de esta sucursal (o los que no tienen sucursal asignada)
                    query_emp = "SELECT id, nombre FROM empleados WHERE estatus = 'Activo' AND (sucursal_base_id = %s OR sucursal_base_id IS NULL) ORDER BY nombre"
                    parametros = (suc_id,)
                
                empleados = ejecutar_query(query_emp, parametros, fetch=True) or []
                
                if not empleados:
                    st.warning("No hay personal asignado a esta sucursal. Activa la rotación arriba si es necesario.")
                else:
                    mapa_emp = {e['nombre']: e['id'] for e in empleados}
                    
                    # 5. Selector de Empleado
                    emp_sel = st.selectbox("👤 Nombre del Colaborador", list(mapa_emp.keys()))
                    emp_id = mapa_emp[emp_sel]

                    st.markdown("<br><br>", unsafe_allow_html=True)
                    
                    # 6. Botones de Acción (Con validación transaccional)
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("✅ MARCAR ENTRADA", use_container_width=True, type="primary"):
                            # Bloqueo: Revisar si ya tiene turno abierto
                            check = ejecutar_query("SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL", (emp_id,), fetch=True)
                            if check:
                                st.error(f"⚠️ {emp_sel}, ya tienes un turno abierto. Marca tu salida primero.")
                            else:
                                exito = ejecutar_query("INSERT INTO asistencia (empleado_id, sucursal_id, entrada, tipo_registro) VALUES (%s, %s, NOW(), 'Normal')", (emp_id, suc_id))
                                if exito is True:
                                    st.success(f"Entrada registrada para {emp_sel} a las {datetime.datetime.now().strftime('%H:%M:%S')}")
                                else:
                                    st.error("Fallo de comunicación con el servidor.")

                    with col2:
                        if st.button("🛑 MARCAR SALIDA", use_container_width=True):
                            # Bloqueo: Buscar el último turno sin cerrar
                            check = ejecutar_query("SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL ORDER BY entrada DESC LIMIT 1", (emp_id,), fetch=True)
                            if not check:
                                st.error(f"⚠️ {emp_sel}, no tienes un turno abierto para marcar salida.")
                            else:
                                reg_id = check[0]['id']
                                exito = ejecutar_query("UPDATE asistencia SET salida = NOW() WHERE id = %s", (reg_id,))
                                if exito is True:
                                    st.success(f"Salida registrada para {emp_sel} a las {datetime.datetime.now().strftime('%H:%M:%S')}")
                                else:
                                    st.error("Fallo de comunicación con el servidor.")
        
    elif seleccion == "📝 Registrar Encargos":
        st.title("📦 Registro de Encargos Especiales")
        st.markdown("Captura las ventas por volumen. El sistema habilitará la captura de bonos según las reglas de negocio.")

        # 1. Carga de catálogos
        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY nombre", fetch=True) or []
        empleados = ejecutar_query("SELECT id, nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre", fetch=True) or []

        if not sucursales or not empleados:
            st.warning("⚠️ Faltan datos de sucursales o empleados activos.")
        else:
            mapa_suc = {s['nombre']: s['id'] for s in sucursales}
            mapa_emp = {e['nombre']: e['id'] for e in empleados}

            # 2. Variables de Reglas de Negocio (Parametrizables)
            UMBRAL_PASTELES_BONO = st.sidebar.number_input("⚙️ Umbral para Bono (Pasteles)", min_value=1, value=5, help="Cambia esto si la meta sube o baja")

            # 3. Interfaz de Captura
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_encargo = st.date_input("Fecha del Encargo", datetime.date.today())
                suc_sel = st.selectbox("Sucursal", list(mapa_suc.keys()))
                vendedor_sel = st.selectbox("Vendedora que cerró la venta", list(mapa_emp.keys()))
            
            with col2:
                cantidad = st.number_input("Cantidad de Pasteles Vendidos", min_value=1, value=1, step=1)
                
                # LÓGICA REACTIVA: Solo mostramos/pedimos el bono si se supera el umbral
                monto_bono = 0.0
                if cantidad >= UMBRAL_PASTELES_BONO:
                    st.success(f"🎉 ¡Meta alcanzada! (>= {UMBRAL_PASTELES_BONO} pasteles).")
                    monto_bono = st.number_input("Monto del Bono Autorizado ($)", min_value=0.0, step=50.0, format="%.2f")
                else:
                    st.info(f"Faltan {UMBRAL_PASTELES_BONO - cantidad} pasteles para habilitar bono.")

            comentarios = st.text_input("Comentarios / Detalles del Cliente (Opcional)")

            # 4. Transacción a Base de Datos
            if st.button("💾 Registrar Encargo y Autorizar", use_container_width=True, type="primary"):
                suc_id = mapa_suc[suc_sel]
                vend_id = mapa_emp[vendedor_sel]
                
                # Como por ahora lo captura el Admin/Encargado, se auto-autoriza y guardamos quién lo hizo (MVP)
                # NOTA: st.session_state.nombre_usuario debe coincidir con un empleado, o por ahora lo dejamos nulo si es el SuperAdmin
                
                query = """
                    INSERT INTO encargos_especiales (sucursal_id, vendedor_id, fecha, cantidad_pasteles, monto_bono, estado, comentarios)
                    VALUES (%s, %s, %s, %s, %s, 'Autorizado', %s)
                """
                exito = ejecutar_query(query, (suc_id, vend_id, fecha_encargo, cantidad, monto_bono, comentarios))
                
                if exito is True:
                    st.toast("Encargo guardado exitosamente", icon="✅")
                    st.rerun()
                else:
                    st.error(f"Error de base de datos: {exito}")

        # 5. Vista Rápida del Historial del Día
        st.markdown("---")
        st.subheader("📋 Encargos Autorizados Recientemente")
        historial = ejecutar_query("""
            SELECT e.fecha, s.nombre as sucursal, emp.nombre as vendedora, e.cantidad_pasteles, e.monto_bono
            FROM encargos_especiales e
            JOIN sucursales s ON e.sucursal_id = s.id
            JOIN empleados emp ON e.vendedor_id = emp.id
            ORDER BY e.id DESC LIMIT 5
        """, fetch=True)
        
        if historial:
            st.dataframe(historial, use_container_width=True)
        else:
            st.caption("No hay encargos registrados recientemente.")
        
    elif seleccion == "👥 Personal":
        st.title("👥 Gestión de Personal")
        st.markdown("Administra la plantilla, asigna roles, esquemas de pago y sucursales base para limitar su visibilidad en el Reloj Checador.")

        # 1. Cargar Catálogos Dinámicos
        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY nombre", fetch=True) or []
        mapa_suc = {s['nombre']: s['id'] for s in sucursales}
        # Añadimos la opción para empleados que cubren descansos en varias sucursales
        opciones_suc = ["Rotación General (Ninguna)"] + list(mapa_suc.keys())
        
        empleados = ejecutar_query("SELECT id, nombre FROM empleados ORDER BY nombre", fetch=True) or []
        mapa_emp = {e['nombre']: e['id'] for e in empleados}
        opciones_emp = ["➕ CREAR NUEVO EMPLEADO"] + list(mapa_emp.keys())

        # 2. Estructura de Pantalla Dividida
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Acción")
            accion_emp = st.selectbox("Selecciona Empleado o Crea Nuevo", opciones_emp)
            
            # Recuperar datos si es modo edición
            datos_edit = None
            if accion_emp != "➕ CREAR NUEVO EMPLEADO":
                emp_id = mapa_emp[accion_emp]
                query_datos = "SELECT * FROM empleados WHERE id = %s"
                datos_edit = ejecutar_query(query_datos, (emp_id,), fetch=True)[0]
                
        with col2:
            st.subheader("Ficha Técnica del Colaborador")
            with st.form("form_personal", clear_on_submit=False):
                # Extracción segura de datos (Manejo estricto de NULLs de la base de datos vieja)
                def_nom = datos_edit['nombre'] if datos_edit else ""
                def_est = datos_edit['estatus'] if datos_edit and datos_edit['estatus'] else "Activo"
                def_rol = datos_edit['rol'] if datos_edit and datos_edit['rol'] in ["Colaborador", "Encargado", "Admin"] else "Colaborador"
                def_tipo_s = datos_edit['tipo_sueldo'] if datos_edit and datos_edit['tipo_sueldo'] in ["Por Hora", "Fijo"] else "Por Hora"
                
                def_ph = float(datos_edit['pago_hora']) if datos_edit and datos_edit['pago_hora'] else 0.0
                def_sf = float(datos_edit['sueldo_fijo_semanal']) if datos_edit and datos_edit['sueldo_fijo_semanal'] else 0.0
                
                # Mapeo inverso: De ID de sucursal a Nombre para el selector visual
                def_suc_id = datos_edit['sucursal_base_id'] if datos_edit else None
                def_suc_nombre = "Rotación General (Ninguna)"
                if def_suc_id:
                    for nom, idx in mapa_suc.items():
                        if idx == def_suc_id:
                            def_suc_nombre = nom
                            break
                try:
                    idx_suc = opciones_suc.index(def_suc_nombre)
                except ValueError:
                    idx_suc = 0
                
                # Campos de Interfaz
                nom_input = st.text_input("Nombre Completo", def_nom)
                
                c1, c2 = st.columns(2)
                est_input = c1.selectbox("Estatus en el Sistema", ["Activo", "Inactivo"], index=0 if def_est == "Activo" else 1)
                rol_input = c2.selectbox("Nivel de Permisos (Rol)", ["Colaborador", "Encargado", "Admin"], index=["Colaborador", "Encargado", "Admin"].index(def_rol))
                
                suc_input = st.selectbox("📍 Sucursal Base (Filtro para Reloj Checador)", opciones_suc, index=idx_suc)
                
                st.markdown("---")
                st.markdown("**Esquema Financiero**")
                c3, c4 = st.columns(2)
                
                # Esquema y montos (Restaurados)
                tipo_s_input = c3.selectbox("Tipo de Sueldo", ["Por Hora", "Fijo"], index=["Por Hora", "Fijo"].index(def_tipo_s))
                ph_input = c4.number_input("Pago por Hora ($)", min_value=0.0, value=def_ph, step=5.0)
                sf_input = c4.number_input("Sueldo Fijo Semanal ($)", min_value=0.0, value=def_sf, step=50.0)
                
                st.markdown("---")
                submit = st.form_submit_button("💾 Guardar Información de Personal", type="primary", use_container_width=True)
                
                # 3. Lógica Transaccional (INSERT vs UPDATE)
                if submit:
                    if not nom_input.strip():
                        st.error("El nombre del colaborador es obligatorio.")
                    else:
                        # Convertir el string visual a ID relacional o NULL
                        final_suc_id = mapa_suc[suc_input] if suc_input != "Rotación General (Ninguna)" else None
                        
                        if accion_emp == "➕ CREAR NUEVO EMPLEADO":
                            q_in = """INSERT INTO empleados (nombre, estatus, pago_hora, tipo_sueldo, sueldo_fijo_semanal, rol, sucursal_base_id)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                            exito = ejecutar_query(q_in, (nom_input, est_input, ph_input, tipo_s_input, sf_input, rol_input, final_suc_id))
                        else:
                            q_up = """UPDATE empleados SET nombre=%s, estatus=%s, pago_hora=%s, tipo_sueldo=%s, sueldo_fijo_semanal=%s, rol=%s, sucursal_base_id=%s
                                      WHERE id=%s"""
                            exito = ejecutar_query(q_up, (nom_input, est_input, ph_input, tipo_s_input, sf_input, rol_input, final_suc_id, emp_id))
                            
                        if exito is True:
                            st.toast("Personal actualizado correctamente", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Error de base de datos: {exito}")
                            
        # 4. Vista Analítica Inferior
        st.markdown("---")
        st.subheader("📋 Plantilla Registrada")
        q_view = """
            SELECT 
                e.nombre as "Nombre", 
                e.estatus as "Estatus", 
                e.rol as "Rol Operativo", 
                COALESCE(s.nombre, '🔄 Rotación General') as "Ubicación Base", 
                e.tipo_sueldo as "Esquema de Pago"
            FROM empleados e
            LEFT JOIN sucursales s ON e.sucursal_base_id = s.id
            ORDER BY e.estatus ASC, e.nombre ASC
        """
        import pandas as pd
        df_view = ejecutar_query(q_view, fetch=True)
        if df_view:
            st.dataframe(pd.DataFrame(df_view), use_container_width=True, hide_index=True)
        
    elif seleccion == "💰 Nómina":
        st.title("💰 Cálculo de Nómina Híbrida")
        st.markdown("Consolida sueldos fijos, pago por horas y suma automáticamente los bonos de encargos autorizados.")

        import pandas as pd # Aseguramos tener pandas para manipular la tabla
        
        # 1. Filtros de Fecha
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            fecha_ini = st.date_input("Fecha Inicio", datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()))
        with col2:
            fecha_fin = st.date_input("Fecha Fin", datetime.date.today())
            
        f_ini_str = fecha_ini.strftime("%Y-%m-%d 00:00:00")
        f_fin_str = fecha_fin.strftime("%Y-%m-%d 23:59:59")

        st.markdown("---")

        if st.button("🚀 Calcular Nómina General", use_container_width=True, type="primary"):
            with st.spinner("Procesando cálculos financieros en la nube..."):
                
                # 2. CONSULTA MAESTRA (Batch Query) ACTUALIZADA
                query_nomina = """
                    SELECT 
                        e.id, 
                        e.nombre,
                        e.tipo_sueldo,
                        e.sueldo_fijo_semanal,
                        e.pago_hora,
                        -- Horas trabajadas
                        COALESCE((SELECT SUM(EXTRACT(EPOCH FROM (salida - entrada))/3600.0) 
                         FROM asistencia WHERE empleado_id = e.id AND entrada >= %s AND salida <= %s), 0) as horas_totales,
                        -- Comisiones base
                        COALESCE((SELECT SUM(monto) FROM comisiones WHERE empleado_id = e.id AND fecha >= %s AND fecha <= %s), 0) as comisiones_base,
                        -- Bonos por Encargos Especiales (NUEVO)
                        COALESCE((SELECT SUM(monto_bono) FROM encargos_especiales WHERE vendedor_id = e.id AND estado = 'Autorizado' AND fecha >= %s AND fecha <= %s), 0) as bonos_encargos,
                        -- Otros Bonos
                        COALESCE((SELECT SUM(monto) FROM ajustes WHERE empleado_id = e.id AND tipo = 'Bono' AND fecha >= %s AND fecha <= %s), 0) as otros_bonos,
                        -- Descuentos
                        COALESCE((SELECT SUM(monto) FROM ajustes WHERE empleado_id = e.id AND tipo = 'Descuento' AND fecha >= %s AND fecha <= %s), 0) as descuentos
                    FROM empleados e
                    WHERE e.estatus = 'Activo'
                    ORDER BY e.nombre
                """
                
                # Pasamos los parámetros de fecha para cada subconsulta
                params = (f_ini_str, f_fin_str, fecha_ini, fecha_fin, fecha_ini, fecha_fin, fecha_ini, fecha_fin, fecha_ini, fecha_fin)
                datos = ejecutar_query(query_nomina, params, fetch=True)

                if datos:
                    # 3. Lógica Financiera en Python (Procesamiento del DataFrame)
                    filas = []
                    for d in datos:
                        # Determinar Sueldo Base según el tipo
                        tipo = d['tipo_sueldo']
                        if tipo == 'Fijo':
                            # Si es fijo, ignoramos las horas y tomamos su cuota
                            sueldo_base = float(d['sueldo_fijo_semanal'])
                            horas_str = "N/A (Fijo)"
                        else:
                            # Si es por hora, multiplicamos
                            sueldo_base = float(d['horas_totales']) * float(d['pago_hora'])
                            horas_str = f"{float(d['horas_totales']):.2f}h"
                        
                        comisiones = float(d['comisiones_base'])
                        bonos_volumen = float(d['bonos_encargos'])
                        bonos_extra = float(d['otros_bonos'])
                        descuentos = float(d['descuentos'])
                        
                        # Cálculo del Neto
                        neto = sueldo_base + comisiones + bonos_volumen + bonos_extra - descuentos
                        
                        filas.append({
                            "Empleado": d['nombre'],
                            "Esquema": tipo,
                            "Horas/Base": horas_str,
                            "Sueldo Base ($)": sueldo_base,
                            "Comisiones ($)": comisiones,
                            "Bono Encargos ($)": bonos_volumen,
                            "Otros Bonos ($)": bonos_extra,
                            "Descuentos ($)": descuentos,
                            "NETO A PAGAR ($)": neto
                        })
                    
                    # 4. RENDERIZADO VISUAL Y KPIS (Dashboard de Encargados)
                    df = pd.DataFrame(filas)
                    
                    # Cálculos totales para los KPIs
                    total_nomina = df["NETO A PAGAR ($)"].sum()
                    total_bonos = df["Bono Encargos ($)"].sum() + df["Otros Bonos ($)"].sum()
                    total_descuentos = df["Descuentos ($)"].sum()

                    st.markdown("### 📊 Resumen Financiero del Periodo")
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    kpi1.metric("Total a Pagar", f"${total_nomina:,.2f}")
                    kpi2.metric("Total Bonos Entregados", f"${total_bonos:,.2f}")
                    kpi3.metric("Total Retenciones (Descuentos)", f"${total_descuentos:,.2f}")
                    kpi4.metric("Colaboradores Pagados", len(df))
                    
                    st.markdown("---")
                    
                    # Formatear columnas a moneda local para la tabla
                    df_visual = df.copy()
                    cols_moneda = ["Sueldo Base ($)", "Comisiones ($)", "Bono Encargos ($)", "Otros Bonos ($)", "Descuentos ($)", "NETO A PAGAR ($)"]
                    for col in cols_moneda:
                        df_visual[col] = df_visual[col].apply(lambda x: f"${x:,.2f}")
                    
                    st.success("Cálculo completado exitosamente.")
                    st.dataframe(df_visual, use_container_width=True, hide_index=True)
                    
                    # 5. MOTOR DE GENERACIÓN DE TICKETS (PDF)
                    st.markdown("### 🖨️ Documentos Operativos")
                    
                    def generar_tickets_pdf(datos_nomina, f_inicio, f_fin):
                        # Configuración de PDF tamaño Ticket/Media Carta (A5)
                        pdf = FPDF(format='A5')
                        pdf.set_auto_page_break(auto=True, margin=15)
                        
                        for emp in datos_nomina:
                            pdf.add_page()
                            pdf.set_font("helvetica", "B", 16)
                            pdf.cell(0, 10, "JESUSITO PASTELERIAS", align="C", new_x="LMARGIN", new_y="NEXT")
                            pdf.set_font("helvetica", "", 10)
                            pdf.cell(0, 5, f"Periodo: {f_inicio} al {f_fin}", align="C", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 5, "-"*50, align="C", new_x="LMARGIN", new_y="NEXT")
                            
                            pdf.set_font("helvetica", "B", 12)
                            pdf.cell(0, 10, f"Colaborador: {emp['Empleado']}", new_x="LMARGIN", new_y="NEXT")
                            
                            pdf.set_font("helvetica", "", 11)
                            pdf.cell(0, 6, f"Esquema: {emp['Esquema']} | Registro: {emp['Horas/Base']}", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 6, f"Sueldo Base: ${emp['Sueldo Base ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 6, f"Comisiones: ${emp['Comisiones ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 6, f"Bono por Meta: ${emp['Bono Encargos ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 6, f"Otros Bonos: ${emp['Otros Bonos ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 6, f"Descuentos: -${emp['Descuentos ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            
                            pdf.cell(0, 5, "-"*50, align="C", new_x="LMARGIN", new_y="NEXT")
                            pdf.set_font("helvetica", "B", 14)
                            pdf.cell(0, 10, f"NETO A PAGAR: ${emp['NETO A PAGAR ($)']:,.2f}", new_x="LMARGIN", new_y="NEXT")
                            
                            # Espacio para firma
                            pdf.set_y(-40)
                            pdf.set_font("helvetica", "", 10)
                            pdf.cell(0, 10, "___________________________________", align="C", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 5, "Firma de Conformidad", align="C", new_x="LMARGIN", new_y="NEXT")
                            
                        return bytes(pdf.output())

                    # Botones de Acción
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        st.download_button(
                            label="📥 Descargar Excel (Contabilidad)",
                            data=df.to_csv(index=False).encode('utf-8'),
                            file_name=f"Nomina_{fecha_ini}_al_{fecha_fin}.csv",
                            mime='text/csv',
                            use_container_width=True
                        )
                    
                    with col_btn2:
                        pdf_bytes = generar_tickets_pdf(filas, fecha_ini, fecha_fin)
                        st.download_button(
                            label="🖨️ Imprimir Tickets (PDF por Lote)",
                            data=pdf_bytes,
                            file_name=f"Tickets_{fecha_ini}_al_{fecha_fin}.pdf",
                            mime='application/pdf',
                            use_container_width=True
                        )
        
    elif seleccion == "⚙️ Permisos y Metas":
        st.title("⚙️ Configuración del Negocio")
        st.markdown("Administración central de infraestructura, reglas de bonificación y seguridad.")

        # Diseño arquitectónico mediante pestañas para modularidad
        tab_suc, tab_metas, tab_permisos = st.tabs(["🏢 Sucursales", "🎯 Metas y Bonos", "🔐 Permisos"])

        # ==========================================
        # TAB 1: INFRAESTRUCTURA (SUCURSALES)
        # ==========================================
        with tab_suc:
            st.subheader("Gestión de Infraestructura Física")
            
            # Formulario de captura
            with st.form("form_sucursal", clear_on_submit=True):
                col_nom, col_btn = st.columns([3, 1])
                nueva_sucursal = col_nom.text_input("Nombre de la nueva sucursal", placeholder="Ej. Matriz, San Ramón, Comitán...")
                
                # Para alinear el botón con el campo de texto
                col_btn.markdown("<br>", unsafe_allow_html=True) 
                submit_suc = col_btn.form_submit_button("➕ Agregar Sucursal", use_container_width=True, type="primary")
                
                if submit_suc:
                    if not nueva_sucursal.strip():
                        st.error("El nombre de la sucursal es obligatorio.")
                    else:
                        # Inserción en la base de datos
                        query = "INSERT INTO sucursales (nombre) VALUES (%s)"
                        exito = ejecutar_query(query, (nueva_sucursal.strip(),))
                        
                        if exito is True:
                            st.toast("Sucursal creada con éxito", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Error de base de datos: {exito}")
            
            # Vista Analítica
            st.markdown("---")
            st.markdown("**Catálogo de Sucursales Activas**")
            
            sucursales_db = ejecutar_query("SELECT id as \"ID\", nombre as \"Nombre de la Sucursal\" FROM sucursales ORDER BY id", fetch=True)
            if sucursales_db:
                import pandas as pd
                st.dataframe(pd.DataFrame(sucursales_db), use_container_width=True, hide_index=True)
            else:
                st.info("No hay sucursales registradas. Utiliza el formulario superior para crear la primera.")

        # ==========================================
        # TAB 2: REGLAS DE NEGOCIO (METAS)
        # ==========================================
        with tab_metas:
            st.subheader("Motor de Reglas Variables")
            st.info("Módulo en construcción: Aquí vincularemos la tabla 'reglas_bonos' para definir el umbral de pasteles y los porcentajes.")

        # ==========================================
        # TAB 3: SEGURIDAD (PERMISOS RBAC)
        # ==========================================
        with tab_permisos:
            st.subheader("Control de Accesos Dinámico")
            st.info("Módulo en construcción: Aquí inyectaremos los interruptores para activar/desactivar módulos por Rol.")

# 6. CONTROLADOR DE FLUJO
if not st.session_state.autenticado:
    mostrar_login()
else:
    mostrar_app()