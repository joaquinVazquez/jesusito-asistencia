import streamlit as st
import datetime
from src.models.db_manager import ejecutar_query
import pandas as pd
from fpdf import FPDF
import io

# 1. CONFIGURACIÓN BASE DE LA PÁGINA (Debe ser la primera instrucción)
st.set_page_config(page_title="Jesusito ERP V3", page_icon="🍰", layout="wide")

# 2. GESTIÓN DE ESTADO (MEMORIA DE SESIÓN)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.rol = None
    st.session_state.nombre_usuario = None

# 3. PATRÓN KIOSCO PÚBLICO Y LOGIN LATERAL
def mostrar_kiosco_publico():
    # --- LOGIN ADMINISTRATIVO (BARRA LATERAL) ---
    with st.sidebar:
        st.image("assets/logo_jesusito.png", use_container_width=True)
        st.markdown("### 🔐 Acceso ERP")
        st.caption("Solo Administración y Encargados")
        
        empleados_admin = ejecutar_query("SELECT nombre, rol, pin FROM empleados WHERE estatus = 'Activo' AND rol IN ('Admin', 'Encargado')", fetch=True) or []
        mapa_admin = {e['nombre']: e for e in empleados_admin}
        
        admin_sel = st.selectbox("Usuario", [""] + list(mapa_admin.keys()))
        pin = st.text_input("PIN", type="password")
        
        if st.button("Ingresar al Sistema", use_container_width=True, type="primary"):
            if admin_sel and pin == str(mapa_admin[admin_sel]['pin']):
                st.session_state.autenticado = True
                st.session_state.rol = mapa_admin[admin_sel]['rol']
                st.session_state.nombre_usuario = mapa_admin[admin_sel]['nombre']
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

    # --- LÓGICA DE SALUDO DINÁMICO ---
    hora_actual = datetime.datetime.now().hour
    if 5 <= hora_actual < 12:
        saludo = "☀️ ¡Buenos días!"
    elif 12 <= hora_actual < 19:
        saludo = "🌤️ ¡Buenas tardes!"
    else:
        saludo = "🌙 ¡Buenas noches!"

    # --- ÁREA PRINCIPAL: RELOJ CHECADOR DE AUTOSERVICIO ---
    st.title(saludo)
    st.markdown("Bienvenido al registro de asistencia. Por favor, selecciona tu ubicación y tu nombre.")

    sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True) or []
    
    if not sucursales:
        st.error("No hay sucursales configuradas en el sistema.")
        return

    mapa_suc = {s['nombre']: s['id'] for s in sucursales}
    
    with st.container(border=True):
        col_suc, col_tog = st.columns([2, 1])
        suc_sel = col_suc.selectbox("📍 Ubicación de la Terminal", list(mapa_suc.keys()))
        suc_id = mapa_suc[suc_sel]
        
        col_tog.markdown("<br>", unsafe_allow_html=True)
        modo_rotacion = col_tog.toggle("🔄 Cubriendo otra sucursal", value=False)

        if modo_rotacion:
            query_emp = "SELECT id, nombre, fecha_nacimiento, fecha_ingreso FROM empleados WHERE estatus = 'Activo' ORDER BY nombre"
            parametros = None
        else:
            query_emp = "SELECT id, nombre, fecha_nacimiento, fecha_ingreso FROM empleados WHERE estatus = 'Activo' AND (sucursal_base_id = %s OR sucursal_base_id IS NULL) ORDER BY nombre"
            parametros = (suc_id,)
        
        empleados = ejecutar_query(query_emp, parametros, fetch=True) or []
        
        if not empleados:
            st.warning("No hay personal asignado a esta sucursal.")
        else:
            mapa_emp = {e['nombre']: e for e in empleados}
            emp_sel = st.selectbox("👤 Nombre del Colaborador", [""] + list(mapa_emp.keys()))
            
            if emp_sel:
                user_data = mapa_emp[emp_sel]
                emp_id = user_data['id']
                hoy = datetime.date.today()

                # --- LÓGICA DE CELEBRACIONES ---
                if user_data['fecha_nacimiento']:
                    fn = user_data['fecha_nacimiento']
                    if fn.month == hoy.month and fn.day == hoy.day:
                        st.success(f"🎉 ¡Feliz Cumpleaños, {emp_sel}! Que tengas un excelente día. 🎂")
                        st.balloons()
                
                if user_data['fecha_ingreso']:
                    fi = user_data['fecha_ingreso']
                    if fi.month == hoy.month and fi.day == hoy.day and fi.year < hoy.year:
                        anios = hoy.year - fi.year
                        st.info(f"🌟 ¡Feliz {anios}° Aniversario en el equipo, {emp_sel}! Gracias por tu dedicación. 🚀")

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ MARCAR ENTRADA", use_container_width=True, type="primary"):
                        check = ejecutar_query("SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL", (emp_id,), fetch=True)
                        if check:
                            st.error(f"⚠️ {emp_sel}, ya tienes un turno abierto. Marca tu salida primero.")
                        else:
                            exito = ejecutar_query("INSERT INTO asistencia (empleado_id, sucursal_id, entrada, tipo_registro) VALUES (%s, %s, NOW(), 'Normal')", (emp_id, suc_id))
                            if exito is True:
                                hora_str = datetime.datetime.now().strftime('%H:%M:%S')
                                st.success(f"¡Excelente turno, {emp_sel}! Tu entrada fue registrada exitosamente a las {hora_str}. ✅")
                                import time; time.sleep(2.5); st.rerun()

                with col2:
                    if st.button("🛑 MARCAR SALIDA", use_container_width=True):
                        check = ejecutar_query("SELECT id FROM asistencia WHERE empleado_id = %s AND salida IS NULL ORDER BY entrada DESC LIMIT 1", (emp_id,), fetch=True)
                        if not check:
                            st.error(f"⚠️ {emp_sel}, no tienes un turno abierto para marcar salida.")
                        else:
                            reg_id = check[0]['id']
                            exito = ejecutar_query("UPDATE asistencia SET salida = NOW() WHERE id = %s", (reg_id,))
                            if exito is True:
                                hora_str = datetime.datetime.now().strftime('%H:%M:%S')
                                st.success(f"¡Buen descanso, {emp_sel}! Tu salida fue registrada exitosamente a las {hora_str}. 🛑")
                                import time; time.sleep(2.5); st.rerun()

# 4. ESTRUCTURA PRINCIPAL (RBAC)
def mostrar_app():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.image("assets/logo_jesusito.png", use_container_width=True)
        st.write(f"👤 **{st.session_state.nombre_usuario}**")
        st.caption(f"Rol: {st.session_state.rol}")
        st.markdown("---")
            
        # Construcción unificada del menú dinámico
        menu = ["⏱️ Reloj Checador"]

        # Módulos compartidos entre Admin y Encargado
        if st.session_state.rol in ["Admin", "Encargado"]:
            menu.extend(["📝 Registrar Encargos", "💰 Nómina"])

        # Módulos exclusivos de la Dirección General (Admin)
        if st.session_state.rol == "Admin":
            menu.extend([
                "👥 Personal",
                "⚙️ Permisos y Metas",
                "🕒 Auditoría Horarios"
            ])

        # Renderizado único con identificador explícito de control
        seleccion = st.radio("Navegación", menu, key="menu_principal_seleccion")
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()

    # --- ENRUTADOR DE VISTAS ---
    if seleccion == "⏱️ Reloj Checador":
        st.title("⏱️ Registro de Asistencia")

        # 1. Obtener metadatos del usuario logueado en tiempo real
        mis_datos = ejecutar_query("SELECT id, sucursal_base_id FROM empleados WHERE nombre = %s", (st.session_state.nombre_usuario,), fetch=True)
        mi_id = mis_datos[0]['id'] if mis_datos else None
        mi_suc_id = mis_datos[0]['sucursal_base_id'] if mis_datos else None

        # 2. Cargar Sucursales
        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY id", fetch=True) or []
        
        if not sucursales:
            st.error("No hay sucursales configuradas en el sistema.")
        else:
            mapa_suc = {s['nombre']: s['id'] for s in sucursales}
            
            with st.container(border=True):
                # ==========================================
                # FLUJO A: AUTOSERVICIO (COLABORADOR)
                # ==========================================
                if st.session_state.rol == 'Colaborador':
                    st.markdown(f"### 👋 Hola, **{st.session_state.nombre_usuario}**")
                    st.markdown("Verifica tu ubicación actual y registra tu turno.")
                    
                    # Preseleccionar su sucursal base automáticamente
                    idx_suc = 0
                    if mi_suc_id and mi_suc_id in mapa_suc.values():
                        idx_suc = list(mapa_suc.values()).index(mi_suc_id)
                        
                    suc_sel = st.selectbox("📍 Ubicación de la Terminal", list(mapa_suc.keys()), index=idx_suc)
                    suc_id = mapa_suc[suc_sel]
                    
                    # Bloqueamos la identidad
                    emp_id = mi_id
                    emp_sel = st.session_state.nombre_usuario

                # ==========================================
                # FLUJO B: MODO KIOSCO (ADMIN / ENCARGADO)
                # ==========================================
                else:
                    st.markdown("### 🏢 Modo Kiosco (Administración)")
                    st.markdown("Tienes privilegios para registrar la asistencia de cualquier elemento de la plantilla.")
                    
                    suc_sel = st.selectbox("📍 Ubicación de la Terminal", list(mapa_suc.keys()))
                    suc_id = mapa_suc[suc_sel]

                    st.markdown("<br>", unsafe_allow_html=True)
                    modo_rotacion = st.toggle("🔄 Personal en rotación (Mostrar plantilla completa)", value=False)

                    if modo_rotacion:
                        query_emp = "SELECT id, nombre FROM empleados WHERE estatus = 'Activo' ORDER BY nombre"
                        parametros = None
                    else:
                        query_emp = "SELECT id, nombre FROM empleados WHERE estatus = 'Activo' AND (sucursal_base_id = %s OR sucursal_base_id IS NULL) ORDER BY nombre"
                        parametros = (suc_id,)
                    
                    empleados = ejecutar_query(query_emp, parametros, fetch=True) or []
                    
                    if not empleados:
                        st.warning("No hay personal asignado a esta sucursal.")
                        emp_id = None
                    else:
                        mapa_emp = {e['nombre']: e['id'] for e in empleados}
                        emp_sel = st.selectbox("👤 Nombre del Colaborador", list(mapa_emp.keys()))
                        emp_id = mapa_emp[emp_sel]

                # ==========================================
                # MOTOR TRANSACCIONAL (Común para ambos flujos)
                # ==========================================
                if emp_id:
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("✅ MARCAR ENTRADA", use_container_width=True, type="primary"):
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
        st.title("📊 Registro Operativo y Bonos")
        st.markdown("Captura encargos por volumen y utiliza la calculadora para inyectar bonos por metas alcanzadas.")

        # 1. Identificar la sucursal del usuario logueado
        mis_datos = ejecutar_query("SELECT sucursal_base_id FROM empleados WHERE nombre = %s", (st.session_state.nombre_usuario,), fetch=True)
        mi_suc_id = mis_datos[0]['sucursal_base_id'] if mis_datos else None

        # 2. Aislamiento de datos según Rol
        if st.session_state.rol == 'Encargado' and mi_suc_id:
            sucursales = ejecutar_query("SELECT id, nombre FROM sucursales WHERE id = %s ORDER BY nombre", (mi_suc_id,), fetch=True) or []
            empleados = ejecutar_query("SELECT id, nombre, sucursal_base_id FROM empleados WHERE estatus = 'Activo' AND (sucursal_base_id = %s OR sucursal_base_id IS NULL) ORDER BY nombre", (mi_suc_id,), fetch=True) or []
        else:
            # Los Administradores ven toda la infraestructura
            sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY nombre", fetch=True) or []
            empleados = ejecutar_query("SELECT id, nombre, sucursal_base_id FROM empleados WHERE estatus = 'Activo' ORDER BY nombre", fetch=True) or []

        if not sucursales or not empleados:
            st.warning("⚠️ Faltan datos de sucursales o empleados activos.")
        else:
            mapa_suc = {s['nombre']: s['id'] for s in sucursales}
            
            # Definición dinámica de pestañas según el Rol
            if st.session_state.rol == 'Admin':
                tab_encargos, tab_ajustes, tab_auditoria = st.tabs(["📦 Encargos por Volumen", "🧮 Calculadora de Ajustes", "🔍 Auditoría Financiera"])
            else:
                tab_encargos, tab_ajustes = st.tabs(["📦 Encargos por Volumen", "🧮 Calculadora de Ajustes"])
                tab_auditoria = None

            # TAB 1: ENCARGOS ESPECIALES (POR VOLUMEN)
            with tab_encargos:
                st.subheader("Registro de Bonos por Volumen de Pasteles")
                
                res_umb = ejecutar_query("SELECT valor FROM config WHERE parametro = 'umbral_pasteles'", fetch=True)
                UMBRAL_PASTELES_BONO = int(res_umb[0]['valor']) if res_umb else 5

                col1, col2 = st.columns(2)
                with col1:
                    fecha_encargo = st.date_input("Fecha del Encargo", datetime.date.today(), key="f_enc")
                    suc_sel_enc = st.selectbox("1. Sucursal", list(mapa_suc.keys()), key="s_enc")
                    
                    suc_enc_id = mapa_suc[suc_sel_enc]
                    emp_enc_filtrados = [e['nombre'] for e in empleados if e['sucursal_base_id'] == suc_enc_id or e['sucursal_base_id'] is None]
                    if not emp_enc_filtrados: emp_enc_filtrados = ["Sin personal"]
                    
                    vendedor_sel = st.selectbox("2. Vendedora", emp_enc_filtrados, key="v_enc")
                
                with col2:
                    cantidad = st.number_input("Cantidad de Pasteles", min_value=1, value=1, step=1)
                    
                    monto_bono = 0.0
                    if cantidad >= UMBRAL_PASTELES_BONO:
                        st.success(f"🎉 Meta alcanzada (>= {UMBRAL_PASTELES_BONO} pasteles).")
                        monto_bono = st.number_input("Bono Autorizado ($)", min_value=0.0, step=50.0, format="%.2f")
                    else:
                        st.info(f"Faltan {UMBRAL_PASTELES_BONO - cantidad} pasteles para habilitar bono.")

                comentarios = st.text_input("Comentarios / Detalles (Opcional)")

                if st.button("💾 Registrar Encargo", use_container_width=True, type="primary"):
                    if vendedor_sel == "Sin personal":
                        st.error("No hay un empleado válido seleccionado.")
                    else:
                        vend_id = next(e['id'] for e in empleados if e['nombre'] == vendedor_sel)
                        query_enc = """
                            INSERT INTO encargos_especiales (sucursal_id, vendedor_id, fecha, cantidad_pasteles, monto_bono, estado, comentarios)
                            VALUES (%s, %s, %s, %s, %s, 'Autorizado', %s)
                        """
                        exito = ejecutar_query(query_enc, (suc_enc_id, vend_id, fecha_encargo, cantidad, monto_bono, comentarios))
                        if exito is True:
                            st.toast("Encargo guardado exitosamente", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Error BD: {exito}")

            # TAB 2: AJUSTES MANUALES Y CALCULADORA
            with tab_ajustes:
                if 'calc_extras' not in st.session_state:
                    st.session_state.calc_extras = 0

                st.subheader("⚖️ Ajustes Manuales Directos (Prioridad Operativa)")
                st.markdown("Inyección inmediata de bonos o descuentos a la nómina.")
                
                with st.container(border=True):
                    c_aj1, c_aj2, c_aj3 = st.columns(3)
                    tipo_manual = c_aj1.selectbox("Tipo de Movimiento", ["Bono Fijo", "Descuento"])
                    fecha_manual = c_aj2.date_input("Fecha de Aplicación", datetime.date.today(), key="f_man")
                    monto_manual = c_aj3.number_input("Monto ($)", min_value=1.0, step=50.0, key="m_man")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    c_aj4, c_aj5, c_aj6 = st.columns([1, 1, 2])
                    suc_man_sel = c_aj4.selectbox("1. Filtrar por Sucursal", ["Todas"] + list(mapa_suc.keys()), key="suc_man")
                    
                    if suc_man_sel == "Todas":
                        emp_manual_filtrados = [e['nombre'] for e in empleados]
                    else:
                        s_id = mapa_suc[suc_man_sel]
                        emp_manual_filtrados = [e['nombre'] for e in empleados if e['sucursal_base_id'] == s_id or e['sucursal_base_id'] is None]
                        
                    if not emp_manual_filtrados: emp_manual_filtrados = ["Sin personal"]
                    
                    emp_manual = c_aj5.selectbox("2. Colaborador", emp_manual_filtrados, key="emp_man")
                    motivo_manual = c_aj6.text_input("3. Motivo del Ajuste", placeholder="Ej. Faltante en caja, Apoyo extra...")
                    
                    if st.button("💾 Guardar Ajuste Manual", type="primary", use_container_width=True):
                        if not motivo_manual.strip() or emp_manual == "Sin personal":
                            st.error("Faltan datos válidos (Motivo o Colaborador).")
                        else:
                            e_man_id = next(e['id'] for e in empleados if e['nombre'] == emp_manual)
                            tipo_sql = "Descuento" if tipo_manual == "Descuento" else "Bono"
                            ejecutar_query("INSERT INTO ajustes (empleado_id, tipo, monto, fecha, motivo) VALUES (%s, %s, %s, %s, %s)", 
                                           (e_man_id, tipo_sql, monto_manual, fecha_manual, motivo_manual))
                            st.success(f"{tipo_manual} de ${monto_manual:,.2f} aplicado a {emp_manual}.")

                st.markdown("---")
                st.subheader("🧮 Calculadora de Metas (Semanal / Festiva)")
                st.markdown("Ingresa la venta real, revisa la vista previa del desglose y confirma la inyección.")
                
                with st.container(border=True):
                    c_calc1, c_calc2 = st.columns(2)
                    suc_sel_calc = c_calc1.selectbox("Sucursal Evaluada", list(mapa_suc.keys()), key="suc_calc")
                    fecha_meta = c_calc2.date_input("Fecha del Cierre", datetime.date.today(), key="f_calc")
                    
                    suc_calc_id = mapa_suc[suc_sel_calc]
                    emp_calc_filtrados = [e['nombre'] for e in empleados if e['sucursal_base_id'] == suc_calc_id or e['sucursal_base_id'] is None]
                    if not emp_calc_filtrados: emp_calc_filtrados = ["Sin personal"]
                    
                    st.markdown("**1. Distribución del Equipo**")
                    c_calc3, c_calc4 = st.columns(2)
                    enc_calc = c_calc3.selectbox("Encargada", emp_calc_filtrados, key="enc_calc")
                    sup_calc = c_calc4.selectbox("Suplente (Opcional)", ["Ninguno"] + emp_calc_filtrados, key="sup_calc")
                    
                    st.markdown("*(Personal de Apoyo)*")
                    for i in range(st.session_state.calc_extras):
                        c_ext1, c_ext2 = st.columns([2, 1])
                        c_ext1.selectbox(f"Colaborador {i+1}", emp_calc_filtrados, key=f"ext_emp_{i}")
                        c_ext2.number_input(f"% Comisión", min_value=0.0, value=1.0, step=0.5, format="%.2f", key=f"ext_pct_{i}")

                    col_add, col_rem = st.columns(2)
                    with col_add:
                        if st.button("➕ Añadir colaborador", use_container_width=True):
                            st.session_state.calc_extras += 1
                            st.rerun()
                    with col_rem:
                        if st.session_state.calc_extras > 0:
                            if st.button("➖ Quitar último", use_container_width=True):
                                st.session_state.calc_extras -= 1
                                st.rerun()
                    
                    st.markdown("**2. Parámetros Financieros**")
                    c_calc5, c_calc6 = st.columns(2)
                    venta_real = c_calc5.number_input("Venta Real Alcanzada ($)", min_value=0.0, step=1000.0)
                    meta_obj = c_calc6.number_input("Meta Establecida ($)", min_value=0.0, value=20000.0, step=1000.0)
                    
                    c_calc7, c_calc8 = st.columns(2)
                    pct_enc = c_calc7.number_input("% Encargada", min_value=0.0, value=3.0, step=0.5)
                    pct_sup = c_calc8.number_input("% Suplente", min_value=0.0, value=1.5, step=0.5)
                    
                    if venta_real > 0:
                        st.markdown("---")
                        st.markdown("### 👁️ Vista Previa de Comisiones")
                        
                        if venta_real >= meta_obj:
                            st.success("✅ Meta Superada. Este es el desglose a pagar:")
                            
                            bono_enc = venta_real * (pct_enc / 100)
                            bono_sup = venta_real * (pct_sup / 100) if sup_calc != "Ninguno" else 0
                            
                            preview_data = [{"Colaborador": enc_calc, "Rol": "Encargada", "Monto a Inyectar": f"${bono_enc:,.2f}"}]
                            if sup_calc != "Ninguno":
                                preview_data.append({"Colaborador": sup_calc, "Rol": "Suplente", "Monto a Inyectar": f"${bono_sup:,.2f}"})
                            
                            for i in range(st.session_state.calc_extras):
                                emp_nombre = st.session_state.get(f"ext_emp_{i}", "Desconocido")
                                emp_porcentaje = st.session_state.get(f"ext_pct_{i}", 0.0)
                                bono_extra = venta_real * (emp_porcentaje / 100)
                                preview_data.append({"Colaborador": emp_nombre, "Rol": f"Apoyo {i+1}", "Monto a Inyectar": f"${bono_extra:,.2f}"})
                                
                            st.table(preview_data)
                            
                            if st.button("⚡ Confirmar e Inyectar a Nómina", use_container_width=True, type="primary"):
                                if enc_calc == "Sin personal":
                                    st.error("Selecciona una encargada válida.")
                                else:
                                    enc_id = next(e['id'] for e in empleados if e['nombre'] == enc_calc)
                                    ejecutar_query("INSERT INTO ajustes (empleado_id, tipo, monto, fecha, motivo) VALUES (%s, 'Bono', %s, %s, 'Bono Meta - Encargada')", (enc_id, bono_enc, fecha_meta))
                                    
                                    if sup_calc != "Ninguno":
                                        sup_id = next(e['id'] for e in empleados if e['nombre'] == sup_calc)
                                        ejecutar_query("INSERT INTO ajustes (empleado_id, tipo, monto, fecha, motivo) VALUES (%s, 'Bono', %s, %s, 'Bono Meta - Suplente')", (sup_id, bono_sup, fecha_meta))
                                        
                                    for i in range(st.session_state.calc_extras):
                                        emp_nombre = st.session_state.get(f"ext_emp_{i}")
                                        emp_porcentaje = st.session_state.get(f"ext_pct_{i}", 0.0)
                                        bono_extra = venta_real * (emp_porcentaje / 100)
                                        ext_id = next(e['id'] for e in empleados if e['nombre'] == emp_nombre)
                                        ejecutar_query("INSERT INTO ajustes (empleado_id, tipo, monto, fecha, motivo) VALUES (%s, 'Bono', %s, %s, 'Bono Meta - Apoyo')", (ext_id, bono_extra, fecha_meta))
                                        
                                    st.toast("Transacciones ejecutadas y sumadas a nómina exitosamente.", icon="✅")
                        else:
                            st.warning(f"La venta (${venta_real:,.2f}) no ha superado la meta (${meta_obj:,.2f}). No hay bonos que repartir.")
        
            # ==========================================
            # TAB 3: AUDITORÍA FINANCIERA (EDICIÓN Y BORRADO)
            # ==========================================
            if tab_auditoria:
                with tab_auditoria:
                    st.subheader("🔍 Auditoría y Corrección de Movimientos")
                st.markdown("Filtra los registros, visualiza la tabla y selecciona el ID específico para editar o eliminar.")

                import time # Necesario para el feedback visual

                # 1. Contenedor de Filtros (UI)
                with st.container(border=True):
                    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                    aud_f_ini = f_col1.date_input("Desde", datetime.date.today() - datetime.timedelta(days=7), key="aud_ini")
                    aud_f_fin = f_col2.date_input("Hasta", datetime.date.today(), key="aud_fin")
                    
                    aud_tipo = f_col3.selectbox("Tipo de Movimiento", ["Todos", "Bono", "Descuento"])
                    
                    # Aprovechamos la variable 'empleados' ya existente en el scope superior
                    opciones_emp = ["Todos"] + [e['nombre'] for e in empleados]
                    aud_emp = f_col4.selectbox("Colaborador", opciones_emp)

                # 2. Motor de Query Dinámica
                query_base = """
                    SELECT a.id, e.nombre as empleado, a.tipo, a.monto, a.fecha, a.motivo
                    FROM ajustes a
                    JOIN empleados e ON a.empleado_id = e.id
                    WHERE a.fecha >= %s AND a.fecha <= %s
                """
                params_aud = [aud_f_ini, aud_f_fin]

                if aud_tipo != "Todos":
                    query_base += " AND a.tipo = %s"
                    params_aud.append(aud_tipo)
                
                if aud_emp != "Todos":
                    query_base += " AND e.nombre = %s"
                    params_aud.append(aud_emp)

                query_base += " ORDER BY a.fecha DESC, a.id DESC"
                
                historial = ejecutar_query(query_base, tuple(params_aud), fetch=True)

                # 3. Renderizado y Edición
                if historial:
                    df_hist = pd.DataFrame(historial)
                    df_visual_hist = df_hist.copy()
                    df_visual_hist['monto'] = df_visual_hist['monto'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(df_visual_hist, use_container_width=True, hide_index=True)

                    st.markdown("### ✏️ Panel de Corrección")
                    
                    # Selector limpio: Solo muestra ID, Nombre y Fecha gracias a los filtros previos
                    opciones_hist = [f"ID: {r['id']} | {r['empleado']} | {r['fecha']}" for r in historial]
                    reg_edit_sel = st.selectbox("Selecciona el movimiento a corregir:", opciones_hist)

                    # Aislamiento del ID para operaciones SQL
                    reg_id = int(reg_edit_sel.split(" |")[0].replace("ID: ", ""))
                    reg_datos = next(r for r in historial if r['id'] == reg_id)

                    with st.form("form_edit_ajuste"):
                        c_ed1, c_ed2 = st.columns(2)
                        nueva_fecha = c_ed1.date_input("Corregir Fecha", reg_datos['fecha'])
                        nuevo_monto = c_ed2.number_input("Corregir Monto ($)", value=float(reg_datos['monto']), step=50.0)

                        nuevo_motivo = st.text_input("Corregir Motivo / Detalles", value=reg_datos['motivo'])

                        col_btn1, col_btn2 = st.columns(2)
                        guardar = col_btn1.form_submit_button("💾 Actualizar Registro", type="primary", use_container_width=True)
                        eliminar = col_btn2.form_submit_button("🗑️ Eliminar Definitivamente", use_container_width=True)

                        # 4. Lógica Transaccional con Feedback Visual
                        if guardar:
                            ejecutar_query("UPDATE ajustes SET fecha = %s, monto = %s, motivo = %s WHERE id = %s", (nueva_fecha, nuevo_monto, nuevo_motivo, reg_id))
                            st.success("✅ Transacción actualizada correctamente. Recargando el sistema...")
                            time.sleep(1.5) # Congela el hilo para permitir el renderizado del mensaje
                            st.rerun()

                        if eliminar:
                            ejecutar_query("DELETE FROM ajustes WHERE id = %s", (reg_id,))
                            st.warning("⚠️ Transacción eliminada de la base de datos.")
                            time.sleep(1.5)
                            st.rerun()
                else:
                    st.info("No hay movimientos financieros que coincidan con los filtros aplicados.")

    elif seleccion == "👥 Personal":
        st.title("👥 Gestión de Personal")
        st.markdown("Administra la plantilla, asigna roles, esquemas de pago y sucursales base para limitar su visibilidad en el Reloj Checador.")

        sucursales = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY nombre", fetch=True) or []
        mapa_suc = {s['nombre']: s['id'] for s in sucursales}
        opciones_suc = ["Rotación General (Ninguna)"] + list(mapa_suc.keys())
        
        empleados = ejecutar_query("SELECT id, nombre FROM empleados ORDER BY nombre", fetch=True) or []
        mapa_emp = {e['nombre']: e['id'] for e in empleados}
        opciones_emp = ["➕ CREAR NUEVO EMPLEADO"] + list(mapa_emp.keys())

        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Acción")
            accion_emp = st.selectbox("Selecciona Empleado o Crea Nuevo", opciones_emp)
            
            datos_edit = None
            if accion_emp != "➕ CREAR NUEVO EMPLEADO":
                emp_id = mapa_emp[accion_emp]
                query_datos = "SELECT * FROM empleados WHERE id = %s"
                datos_edit = ejecutar_query(query_datos, (emp_id,), fetch=True)[0]
                
        with col2:
            st.subheader("Ficha Técnica del Colaborador")
            with st.form("form_personal", clear_on_submit=False):
                # 1. Extracción de datos básicos
                def_nom = datos_edit['nombre'] if datos_edit else ""
                def_est = datos_edit['estatus'] if datos_edit and datos_edit['estatus'] else "Activo"
                def_rol = datos_edit['rol'] if datos_edit and datos_edit['rol'] in ["Colaborador", "Encargado", "Admin"] else "Colaborador"
                def_tipo_s = datos_edit['tipo_sueldo'] if datos_edit and datos_edit['tipo_sueldo'] in ["Por Hora", "Fijo"] else "Por Hora"
                
                # 2. Extracción de Fechas
                def_fn = datos_edit['fecha_nacimiento'] if datos_edit and datos_edit['fecha_nacimiento'] else None
                def_fi = datos_edit['fecha_ingreso'] if datos_edit and datos_edit['fecha_ingreso'] else None
                
                # 3. Extracción de montos financieros
                def_ph = float(datos_edit['pago_hora']) if datos_edit and datos_edit['pago_hora'] else 0.0
                def_sf = float(datos_edit['sueldo_fijo_semanal']) if datos_edit and datos_edit['sueldo_fijo_semanal'] else 0.0
                
                # 4. RECUPERACIÓN DE idx_suc
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

                # --- CAMPOS DE INTERFAZ ---
                nom_input = st.text_input("Nombre Completo", def_nom)
                
                c1, c2 = st.columns(2)
                est_input = c1.selectbox("Estatus en el Sistema", ["Activo", "Inactivo"], index=0 if def_est == "Activo" else 1)
                rol_input = c2.selectbox("Nivel de Permisos (Rol)", ["Colaborador", "Encargado", "Admin"], index=["Colaborador", "Encargado", "Admin"].index(def_rol))
                
                suc_input = st.selectbox("📍 Sucursal Base (Filtro para Reloj Checador)", opciones_suc, index=idx_suc)
                
                # --- CAMPOS DE FECHA ---
                st.markdown("---")
                st.markdown("**Fechas Importantes (Kiosco / Celebraciones)**")
                cf1, cf2 = st.columns(2)
                fn_input = cf1.date_input("Fecha de Nacimiento", value=def_fn, min_value=datetime.date(1950, 1, 1), max_value=datetime.date.today())
                fi_input = cf2.date_input("Fecha de Ingreso", value=def_fi, min_value=datetime.date(2010, 1, 1), max_value=datetime.date.today())

                # --- ESQUEMA FINANCIERO ---
                st.markdown("---")
                st.markdown("**Esquema Financiero**")
                c3, c4 = st.columns(2)
                
                tipo_s_input = c3.selectbox("Tipo de Sueldo", ["Por Hora", "Fijo"], index=["Por Hora", "Fijo"].index(def_tipo_s))
                ph_input = c4.number_input("Pago por Hora ($)", min_value=0.0, value=def_ph, step=5.0)
                sf_input = c4.number_input("Sueldo Fijo Semanal ($)", min_value=0.0, value=def_sf, step=50.0)
                
                # --- PIN ---
                st.markdown("---")
                pin_input = st.text_input("PIN de Acceso (Solo Admin/Encargados)", 
                                         value=datos_edit['pin'] if datos_edit and datos_edit['pin'] else "", 
                                         type="password", 
                                         help="Clave numérica para acceder a módulos administrativos.")
                
                # --- BOTÓN Y LÓGICA DE GUARDADO ---
                st.markdown("---")
                submit = st.form_submit_button("💾 Guardar Información de Personal", type="primary", use_container_width=True)
                
                if submit:
                    if not nom_input.strip():
                        st.error("El nombre del colaborador es obligatorio.")
                    else:
                        final_suc_id = mapa_suc[suc_input] if suc_input != "Rotación General (Ninguna)" else None
                        
                        if accion_emp == "➕ CREAR NUEVO EMPLEADO":
                            q_in = """INSERT INTO empleados (nombre, estatus, pago_hora, tipo_sueldo, sueldo_fijo_semanal, rol, sucursal_base_id, pin, fecha_nacimiento, fecha_ingreso)
                                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                            exito = ejecutar_query(q_in, (nom_input, est_input, ph_input, tipo_s_input, sf_input, rol_input, final_suc_id, pin_input, fn_input, fi_input))
                        else:
                            q_up = """UPDATE empleados SET nombre=%s, estatus=%s, pago_hora=%s, tipo_sueldo=%s, sueldo_fijo_semanal=%s, rol=%s, sucursal_base_id=%s, pin=%s, fecha_nacimiento=%s, fecha_ingreso=%s
                                      WHERE id=%s"""
                            exito = ejecutar_query(q_up, (nom_input, est_input, ph_input, tipo_s_input, sf_input, rol_input, final_suc_id, pin_input, fn_input, fi_input, emp_id))
                            
                        if exito is True:
                            import time
                            st.success("✅ El registro del colaborador se actualizó correctamente. Recargando...")
                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error(f"Error de base de datos: {exito}")
                            
        # --- TABLA DE PLANTILLA ---
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
        df_view = ejecutar_query(q_view, fetch=True)
        if df_view:
            st.dataframe(pd.DataFrame(df_view), use_container_width=True, hide_index=True)
        
    elif seleccion == "💰 Nómina":
        st.title("💰 Cálculo de Nómina Híbrida")
        st.markdown("Consolida sueldos fijos, pago por horas y suma automáticamente los bonos de encargos autorizados.")
        
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
                # Obtener la sucursal del Encargado
                mis_datos = ejecutar_query("SELECT sucursal_base_id FROM empleados WHERE nombre = %s", (st.session_state.nombre_usuario,), fetch=True)
                mi_suc_id = mis_datos[0]['sucursal_base_id'] if mis_datos else None

                # Base de la consulta
                query_nomina = """
                    SELECT 
                        e.id, 
                        e.nombre,
                        e.tipo_sueldo,
                        e.sueldo_fijo_semanal,
                        e.pago_hora,
                        COALESCE((SELECT SUM(EXTRACT(EPOCH FROM (salida - entrada))/3600.0) 
                         FROM asistencia WHERE empleado_id = e.id AND entrada >= %s AND salida <= %s), 0) as horas_totales,
                        COALESCE((SELECT SUM(monto) FROM comisiones WHERE empleado_id = e.id AND fecha >= %s AND fecha <= %s), 0) as comisiones_base,
                        COALESCE((SELECT SUM(monto_bono) FROM encargos_especiales WHERE vendedor_id = e.id AND estado = 'Autorizado' AND fecha >= %s AND fecha <= %s), 0) as bonos_encargos,
                        COALESCE((SELECT SUM(monto) FROM ajustes WHERE empleado_id = e.id AND tipo = 'Bono' AND fecha >= %s AND fecha <= %s), 0) as otros_bonos,
                        COALESCE((SELECT SUM(monto) FROM ajustes WHERE empleado_id = e.id AND tipo = 'Descuento' AND fecha >= %s AND fecha <= %s), 0) as descuentos
                    FROM empleados e
                    WHERE e.estatus = 'Activo'
                """
                
                params = [f_ini_str, f_fin_str, fecha_ini, fecha_fin, fecha_ini, fecha_fin, fecha_ini, fecha_fin, fecha_ini, fecha_fin]
                
                # Inyección de seguridad por Rol (Aislamiento de Sucursal)
                if st.session_state.rol == 'Encargado' and mi_suc_id:
                    query_nomina += " AND (e.sucursal_base_id = %s OR e.sucursal_base_id IS NULL)"
                    params.append(mi_suc_id)
                    
                query_nomina += " ORDER BY e.nombre"
                
                datos = ejecutar_query(query_nomina, tuple(params), fetch=True)

                if datos:
                    filas = []
                    for d in datos:
                        tipo = d['tipo_sueldo']
                        if tipo == 'Fijo':
                            sueldo_base = float(d['sueldo_fijo_semanal'])
                            horas_str = "N/A (Fijo)"
                        else:
                            sueldo_base = float(d['horas_totales']) * float(d['pago_hora'])
                            horas_str = f"{float(d['horas_totales']):.2f}h"
                        
                        comisiones = float(d['comisiones_base'])
                        bonos_volumen = float(d['bonos_encargos'])
                        bonos_extra = float(d['otros_bonos'])
                        descuentos = float(d['descuentos'])
                        
                        # DEPURACIÓN: Omitir si es "Por Hora" y no tiene ningún tipo de actividad financiera
                        if tipo == 'Por Hora' and sueldo_base == 0 and comisiones == 0 and bonos_volumen == 0 and bonos_extra == 0 and descuentos == 0:
                            continue
                        
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
                    
                    if not filas:
                        st.warning("No hay datos de nómina para mostrar en este periodo con la plantilla actual de tu sucursal.")
                        st.stop()
                        
                    df = pd.DataFrame(filas)
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
                    
                    df_visual = df.copy()
                    cols_moneda = ["Sueldo Base ($)", "Comisiones ($)", "Bono Encargos ($)", "Otros Bonos ($)", "Descuentos ($)", "NETO A PAGAR ($)"]
                    for col in cols_moneda:
                        df_visual[col] = df_visual[col].apply(lambda x: f"${x:,.2f}")
                    
                    st.success("Cálculo completado exitosamente.")
                    st.dataframe(df_visual, use_container_width=True, hide_index=True)
                    
                    st.markdown("### 🖨️ Documentos Operativos")
                    
                    def generar_tickets_pdf(datos_nomina, f_inicio, f_fin):
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
                            
                            pdf.set_y(-40)
                            pdf.set_font("helvetica", "", 10)
                            pdf.cell(0, 10, "___________________________________", align="C", new_x="LMARGIN", new_y="NEXT")
                            pdf.cell(0, 5, "Firma de Conformidad", align="C", new_x="LMARGIN", new_y="NEXT")
                            
                        return bytes(pdf.output())

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
                else:
                    st.warning("No se encontraron colaboradores activos.")
        
    elif seleccion == "⚙️ Permisos y Metas":
        st.title("⚙️ Configuración del Negocio")
        st.markdown("Administración central de infraestructura, reglas de bonificación y seguridad.")

        tab_suc, tab_metas, tab_permisos = st.tabs(["🏢 Sucursales", "🎯 Metas y Bonos", "🔐 Permisos"])

        with tab_suc:
            st.subheader("Gestión de Infraestructura Física")
            with st.form("form_sucursal", clear_on_submit=True):
                col_nom, col_btn = st.columns([3, 1])
                nueva_sucursal = col_nom.text_input("Nombre de la nueva sucursal", placeholder="Ej. Matriz, San Ramón, Comitán...")
                
                col_btn.markdown("<br>", unsafe_allow_html=True) 
                submit_suc = col_btn.form_submit_button("➕ Agregar Sucursal", use_container_width=True, type="primary")
                
                if submit_suc:
                    if not nueva_sucursal.strip():
                        st.error("El nombre de la sucursal es obligatorio.")
                    else:
                        query = "INSERT INTO sucursales (nombre) VALUES (%s)"
                        exito = ejecutar_query(query, (nueva_sucursal.strip(),))
                        
                        if exito is True:
                            st.toast("Sucursal creada con éxito", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Error de base de datos: {exito}")
            
            st.markdown("---")
            st.markdown("**Catálogo de Sucursales Activas**")
            
            sucursales_db = ejecutar_query("SELECT id as \"ID\", nombre as \"Nombre de la Sucursal\" FROM sucursales ORDER BY id", fetch=True)
            if sucursales_db:
                st.dataframe(pd.DataFrame(sucursales_db), use_container_width=True, hide_index=True)
            else:
                st.info("No hay sucursales registradas. Utiliza el formulario superior para crear la primera.")

        with tab_metas:
            st.subheader("📦 Parámetros Globales (Encargos Especiales)")
            
            check_umbral = ejecutar_query("SELECT valor FROM config WHERE parametro = 'umbral_pasteles'", fetch=True)
            if not check_umbral:
                ejecutar_query("INSERT INTO config (parametro, valor) VALUES ('umbral_pasteles', '5')")
                umbral_actual = 5
            else:
                umbral_actual = int(check_umbral[0]['valor'])
                
            with st.form("form_config_global", clear_on_submit=False):
                col_umb, col_btn_umb = st.columns([3, 1])
                nuevo_umbral = col_umb.number_input("Umbral mínimo de pasteles para habilitar bono", min_value=1, value=umbral_actual)
                
                col_btn_umb.markdown("<br>", unsafe_allow_html=True)
                btn_global = col_btn_umb.form_submit_button("💾 Guardar Umbral", type="primary", use_container_width=True)
                
                if btn_global:
                    exito = ejecutar_query("UPDATE config SET valor = %s WHERE parametro = 'umbral_pasteles'", (str(nuevo_umbral),))
                    if exito is True:
                        st.toast("Umbral global actualizado. El módulo de encargos ahora respetará esta regla.", icon="✅")
                        st.rerun()

            st.markdown("---")
            st.subheader("📈 Metas de Venta por Sucursal y Periodo")
            st.markdown("Define metas semanales para la operación normal, o metas de evento para fechas festivas.")

            sucursales_meta = ejecutar_query("SELECT id, nombre FROM sucursales ORDER BY nombre", fetch=True) or []
            mapa_suc_meta = {s['nombre']: s['id'] for s in sucursales_meta}

            with st.form("form_reglas_bonos", clear_on_submit=True):
                c_per1, c_per2 = st.columns(2)
                periodo_sel = c_per1.selectbox("Periodicidad de la Meta", ["Semanal", "Diaria", "Mensual", "Evento Festivo"])
                evento_input = c_per2.text_input("Nombre del Evento (Solo si aplica)", placeholder="Ej. Día del Niño, Día de las Madres")
                
                st.markdown("---")
                c1, c2, c3, c4 = st.columns(4)
                
                opciones_suc = list(mapa_suc_meta.keys()) if mapa_suc_meta else ["Sin sucursales"]
                suc_sel = c1.selectbox("Sucursal Objetivo", opciones_suc)
                
                meta_input = c2.number_input("Venta Meta ($)", min_value=0.0, step=1000.0)
                pct_enc = c3.number_input("% Encargada", min_value=0.0, step=0.5, format="%.2f")
                pct_sup = c4.number_input("% Suplente", min_value=0.0, step=0.5, format="%.2f")
                
                st.markdown("<br>", unsafe_allow_html=True)
                btn_meta = st.form_submit_button("➕ Asignar Regla", use_container_width=True, type="primary")
                
                if btn_meta and mapa_suc_meta:
                    if periodo_sel == "Evento Festivo" and not evento_input.strip():
                        st.error("Debes especificar el nombre del evento.")
                    else:
                        suc_id = mapa_suc_meta[suc_sel]
                        nombre_ev_final = evento_input.strip() if periodo_sel == "Evento Festivo" else None
                        
                        q_desact = "UPDATE reglas_bonos SET activo = FALSE WHERE sucursal_id = %s AND periodicidad = %s"
                        ejecutar_query(q_desact, (suc_id, periodo_sel))
                        
                        q_ins = """
                            INSERT INTO reglas_bonos (sucursal_id, venta_meta, porcentaje_encargada, porcentaje_suplente, periodicidad, nombre_evento, activo) 
                            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                        """
                        exito = ejecutar_query(q_ins, (suc_id, meta_input, pct_enc, pct_sup, periodo_sel, nombre_ev_final))
                        
                        if exito is True:
                            st.toast(f"Regla {periodo_sel} activada para {suc_sel}", icon="✅")
                            st.rerun()
                        else:
                            st.error(f"Error de base de datos: {exito}")

            st.markdown("**Matriz de Reglas Activas**")
            q_reglas = """
                SELECT 
                    s.nombre as "Sucursal",
                    r.periodicidad as "Periodo",
                    COALESCE(r.nombre_evento, '-') as "Evento",
                    r.venta_meta as "Meta ($)", 
                    r.porcentaje_encargada as "% Enc.", 
                    r.porcentaje_suplente as "% Sup."
                FROM reglas_bonos r
                JOIN sucursales s ON r.sucursal_id = s.id
                WHERE r.activo = TRUE
                ORDER BY s.nombre, r.periodicidad
            """
            reglas_db = ejecutar_query(q_reglas, fetch=True)
            if reglas_db:
                df_reglas = pd.DataFrame(reglas_db)
                df_reglas["Meta ($)"] = df_reglas["Meta ($)"].apply(lambda x: f"${x:,.2f}")
                df_reglas["% Enc."] = df_reglas["% Enc."].apply(lambda x: f"{x}%")
                df_reglas["% Sup."] = df_reglas["% Sup."].apply(lambda x: f"{x}%")
                st.dataframe(df_reglas, use_container_width=True, hide_index=True)
            else:
                st.caption("No hay metas establecidas en este momento.")

        with tab_permisos:
            st.subheader("Control de Accesos Dinámico")
            st.info("Módulo en construcción: Aquí inyectaremos los interruptores para activar/desactivar módulos por Rol.")

    elif seleccion == "🕒 Auditoría Horarios":
        st.title("🕒 Auditoría y Corrección de Horarios")
        st.markdown("Módulo exclusivo para Administración. Corrige turnos huérfanos (olvido de salida) o errores de registro.")

        empleados = ejecutar_query("SELECT id, nombre FROM empleados ORDER BY nombre", fetch=True) or []
        
        if not empleados:
            st.warning("No hay empleados registrados en el sistema.")
        else:
            mapa_emp = {e['nombre']: e['id'] for e in empleados}
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                emp_sel = c1.selectbox("👤 Seleccionar Colaborador", list(mapa_emp.keys()))
                f_ini = c2.date_input("📅 Desde", datetime.date.today() - datetime.timedelta(days=7))
                f_fin = c3.date_input("📅 Hasta", datetime.date.today())
            
            emp_id = mapa_emp[emp_sel]
            
            query_asis = """
                SELECT id, entrada, salida, tipo_registro
                FROM asistencia 
                WHERE empleado_id = %s AND DATE(entrada) >= %s AND DATE(entrada) <= %s
                ORDER BY entrada DESC
            """
            registros = ejecutar_query(query_asis, (emp_id, f_ini, f_fin), fetch=True)
            
            st.markdown("---")
            if registros:
                df_asis = pd.DataFrame(registros)
                df_asis['entrada'] = pd.to_datetime(df_asis['entrada']).dt.strftime('%Y-%m-%d %H:%M:%S')
                df_asis['salida'] = pd.to_datetime(df_asis['salida']).dt.strftime('%Y-%m-%d %H:%M:%S').fillna('Pendiente / Sin Salida')
                st.dataframe(df_asis, use_container_width=True, hide_index=True)
                
                st.subheader("✏️ Corregir Registro Específico")
                
                opciones_reg = [f"ID: {r['id']} | Entrada: {r['entrada'].strftime('%Y-%m-%d %H:%M') if isinstance(r['entrada'], datetime.datetime) else r['entrada']}" for r in registros]
                reg_sel = st.selectbox("Selecciona el turno que deseas modificar", opciones_reg)
                
                reg_id = int(reg_sel.split(" |")[0].replace("ID: ", ""))
                reg_datos = next(r for r in registros if r['id'] == reg_id)
                
                ent_dt = reg_datos['entrada'] if isinstance(reg_datos['entrada'], datetime.datetime) else pd.to_datetime(reg_datos['entrada'])
                tiene_salida = pd.notnull(reg_datos['salida'])
                sal_dt = reg_datos['salida'] if tiene_salida and isinstance(reg_datos['salida'], datetime.datetime) else (pd.to_datetime(reg_datos['salida']) if tiene_salida else None)
                
                with st.form("form_edicion_horario", clear_on_submit=False):
                    col_e, col_s = st.columns(2)
                    
                    with col_e:
                        st.markdown("**Marca de Entrada**")
                        new_ent_d = st.date_input("Fecha Entrada", ent_dt.date())
                        new_ent_t = st.time_input("Hora Entrada", ent_dt.time())
                        
                    with col_s:
                        st.markdown("**Marca de Salida**")
                        aplicar_salida = st.checkbox("Turno cerrado (Habilitar salida)", value=tiene_salida, help="Desmarca esto si quieres borrar la hora de salida.")
                        
                        sugerencia_d = sal_dt.date() if tiene_salida else new_ent_d
                        sugerencia_t = sal_dt.time() if tiene_salida else datetime.datetime.now().time()
                        
                        new_sal_d = st.date_input("Fecha Salida", sugerencia_d, disabled=not aplicar_salida)
                        new_sal_t = st.time_input("Hora Salida", sugerencia_t, disabled=not aplicar_salida)

                    st.markdown("---")
                    if st.form_submit_button("💾 Sobreescribir Turno en Base de Datos", type="primary", use_container_width=True):
                        final_ent = datetime.datetime.combine(new_ent_d, new_ent_t)
                        final_sal = datetime.datetime.combine(new_sal_d, new_sal_t) if aplicar_salida else None
                        
                        if final_sal and final_sal <= final_ent:
                            st.error("Error Lógico: La salida no puede ser anterior o igual a la entrada.")
                        else:
                            q_update = "UPDATE asistencia SET entrada = %s, salida = %s WHERE id = %s"
                            exito = ejecutar_query(q_update, (final_ent, final_sal, reg_id))
                            
                            if exito is True:
                                st.success("Registro corregido. El motor de nómina ya tomará este nuevo horario.")
                            else:
                                st.error(f"Error BD: {exito}")
            else:
                st.info("El colaborador no tiene registros de asistencia en el rango de fechas seleccionado.")

# 5. CONTROLADOR DE FLUJO
if not st.session_state.autenticado:
    mostrar_kiosco_publico()
else:
    mostrar_app()