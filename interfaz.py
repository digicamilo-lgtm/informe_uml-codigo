"""Interfaz grafica de EcoTech Solutions.

Este archivo contiene unicamente la interfaz de usuario. El modelo UML, la
validacion y la persistencia SQLite permanecen en ecotech.py para mantener
separadas presentacion y logica de negocio.
"""

from __future__ import annotations

from datetime import date
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import ecotech


class EcoTechApp(tk.Tk):
    """Ventana principal para operar el sistema EcoTech."""

    def __init__(self) -> None:
        super().__init__()
        self.title("EcoTech Solutions | Gestion empresarial")
        self.geometry("1120x700")
        self.minsize(900, 560)
        self.conexion = ecotech.inicializar_bd("ecotech.db")
        self._configurar_estilos()
        self._crear_interfaz()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _configurar_estilos(self) -> None:
        """Configura colores y dimensiones comunes de la interfaz."""
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        estilo.configure("Subtitle.TLabel", foreground="#52606d")
        estilo.configure("Accent.TButton", padding=7)
        estilo.configure("Treeview", rowheight=28)

    def _crear_interfaz(self) -> None:
        """Crea la cabecera, las pestañas y sus controles operativos."""
        cabecera = ttk.Frame(self, padding=(22, 18, 22, 8))
        cabecera.pack(fill="x")
        ttk.Label(cabecera, text="EcoTech Solutions", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            cabecera,
            text="Panel de gestion de departamentos, personas, proyectos y horas",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(4, 18))
        self._crear_tab_departamentos()
        self._crear_tab_empleados()
        self._crear_tab_proyectos()
        self._crear_tab_registros()

    def _tab_base(self, titulo: str) -> tuple[ttk.Frame, ttk.Frame]:
        """Devuelve un tab con formulario superior y tabla inferior."""
        tab = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(tab, text=titulo)
        formulario = ttk.LabelFrame(tab, text="Datos", padding=12)
        formulario.pack(fill="x", pady=(0, 12))
        tabla = ttk.Frame(tab)
        tabla.pack(fill="both", expand=True)
        return formulario, tabla

    @staticmethod
    def _campo(parent: ttk.Frame, etiqueta: str, fila: int, columna: int) -> ttk.Entry:
        """Crea una etiqueta y un campo de texto en una cuadricula."""
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=columna, sticky="w", padx=(0, 6), pady=5)
        campo = ttk.Entry(parent, width=22)
        campo.grid(row=fila, column=columna + 1, sticky="ew", padx=(0, 14), pady=5)
        return campo

    @staticmethod
    def _tabla(parent: ttk.Frame, columnas: list[tuple[str, int]]) -> ttk.Treeview:
        """Crea una tabla con scroll vertical para resultados CRUD."""
        nombres = [nombre for nombre, _ in columnas]
        tabla = ttk.Treeview(parent, columns=nombres, show="headings")
        for nombre, ancho in columnas:
            tabla.heading(nombre, text=nombre.replace("_", " ").title())
            tabla.column(nombre, width=ancho, anchor="w")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tabla

    def _crear_tab_departamentos(self) -> None:
        """Construye el mantenimiento de departamentos."""
        formulario, tabla = self._tab_base("Departamentos")
        self.dept_id = self._campo(formulario, "ID", 0, 0)
        self.dept_nombre = self._campo(formulario, "Nombre", 0, 2)
        ttk.Button(formulario, text="Crear", command=self._crear_departamento, style="Accent.TButton").grid(row=0, column=4, padx=4)
        ttk.Button(formulario, text="Actualizar nombre", command=self._actualizar_departamento).grid(row=0, column=5, padx=4)
        ttk.Button(formulario, text="Eliminar", command=self._eliminar_departamento).grid(row=0, column=6, padx=4)
        self.tabla_dept = self._tabla(tabla, [("id_dept", 100), ("nombre_dept", 300), ("gerente_id", 140)])
        self._refrescar_departamentos()

    def _crear_tab_empleados(self) -> None:
        """Construye el mantenimiento de empleados."""
        formulario, tabla = self._tab_base("Empleados")
        self.emp_id = self._campo(formulario, "ID", 0, 0)
        self.emp_nombre = self._campo(formulario, "Nombre", 0, 2)
        self.emp_correo = self._campo(formulario, "Correo", 0, 4)
        self.emp_direccion = self._campo(formulario, "Direccion", 1, 0)
        self.emp_telefono = self._campo(formulario, "Telefono", 1, 2)
        self.emp_salario = self._campo(formulario, "Salario", 1, 4)
        self.emp_departamento = self._campo(formulario, "ID departamento", 2, 0)
        ttk.Button(formulario, text="Crear empleado", command=self._crear_empleado, style="Accent.TButton").grid(row=2, column=2, padx=4)
        ttk.Button(formulario, text="Actualizar salario", command=self._actualizar_empleado).grid(row=2, column=4, padx=4)
        ttk.Button(formulario, text="Eliminar", command=self._eliminar_empleado).grid(row=2, column=5, padx=4)
        self.tabla_emp = self._tabla(tabla, [("id", 60), ("nombre", 150), ("correo", 200), ("salario", 100), ("departamento", 120)])
        self._refrescar_empleados()

    def _crear_tab_proyectos(self) -> None:
        """Construye el mantenimiento de proyectos."""
        formulario, tabla = self._tab_base("Proyectos")
        self.proy_id = self._campo(formulario, "ID", 0, 0)
        self.proy_nombre = self._campo(formulario, "Nombre", 0, 2)
        self.proy_descripcion = self._campo(formulario, "Descripcion", 0, 4)
        self.proy_estado = self._campo(formulario, "Estado", 1, 0)
        ttk.Button(formulario, text="Crear proyecto", command=self._crear_proyecto, style="Accent.TButton").grid(row=1, column=2, padx=4)
        ttk.Button(formulario, text="Actualizar estado", command=self._actualizar_proyecto).grid(row=1, column=4, padx=4)
        ttk.Button(formulario, text="Eliminar", command=self._eliminar_proyecto).grid(row=1, column=5, padx=4)
        self.tabla_proy = self._tabla(tabla, [("id_proyecto", 100), ("nombre", 180), ("descripcion", 280), ("estado", 140)])
        self._refrescar_proyectos()

    def _crear_tab_registros(self) -> None:
        """Construye el mantenimiento de registros de tiempo."""
        formulario, tabla = self._tab_base("Registro de horas")
        self.reg_id = self._campo(formulario, "ID", 0, 0)
        self.reg_fecha = self._campo(formulario, "Fecha", 0, 2)
        self.reg_horas = self._campo(formulario, "Horas", 0, 4)
        self.reg_descripcion = self._campo(formulario, "Descripcion", 1, 0)
        self.reg_empleado = self._campo(formulario, "ID empleado", 1, 2)
        self.reg_proyecto = self._campo(formulario, "ID proyecto", 1, 4)
        ttk.Button(formulario, text="Crear registro", command=self._crear_registro, style="Accent.TButton").grid(row=2, column=2, padx=4)
        ttk.Button(formulario, text="Actualizar horas", command=self._actualizar_registro).grid(row=2, column=4, padx=4)
        ttk.Button(formulario, text="Eliminar", command=self._eliminar_registro).grid(row=2, column=5, padx=4)
        self.tabla_reg = self._tabla(tabla, [("id_registro", 100), ("fecha", 120), ("horas", 90), ("descripcion", 260), ("empleado_id", 110), ("proyecto_id", 110)])
        self._refrescar_registros()

    def _numero(self, campo: ttk.Entry, etiqueta: str) -> int:
        """Convierte un campo a entero y produce un mensaje amigable."""
        try:
            valor = int(campo.get())
        except ValueError as error:
            raise ValueError(f"{etiqueta} debe ser un numero entero.") from error
        return valor

    def _ejecutar(self, accion) -> None:
        """Ejecuta una accion y muestra errores sin cerrar la interfaz."""
        try:
            accion()
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("No se pudo completar la operacion", str(error), parent=self)

    def _crear_departamento(self) -> None:
        self._ejecutar(lambda: (ecotech.crear_departamento(self.conexion, ecotech.Departamento(self._numero(self.dept_id, "ID"), self.dept_nombre.get())), self._refrescar_departamentos()))

    def _actualizar_departamento(self) -> None:
        self._ejecutar(lambda: (ecotech.actualizar_departamento(self.conexion, self._numero(self.dept_id, "ID"), self.dept_nombre.get()), self._refrescar_departamentos()))

    def _eliminar_departamento(self) -> None:
        self._ejecutar(lambda: (ecotech.eliminar_departamento(self.conexion, self._numero(self.dept_id, "ID")), self._refrescar_departamentos(), self._refrescar_empleados()))

    def _crear_empleado(self) -> None:
        def accion() -> None:
            empleado = ecotech.Empleado(self._numero(self.emp_id, "ID"), self.emp_nombre.get(), self.emp_correo.get(), self.emp_direccion.get(), self.emp_telefono.get(), self.emp_salario.get(), date.today(), self._numero(self.emp_departamento, "ID departamento") if self.emp_departamento.get() else None)
            ecotech.crear_empleado(self.conexion, empleado)
            self._refrescar_empleados()
        self._ejecutar(accion)

    def _actualizar_empleado(self) -> None:
        self._ejecutar(lambda: (ecotech.actualizar_empleado(self.conexion, self._numero(self.emp_id, "ID"), self.emp_salario.get()), self._refrescar_empleados()))

    def _eliminar_empleado(self) -> None:
        self._ejecutar(lambda: (ecotech.eliminar_empleado(self.conexion, self._numero(self.emp_id, "ID")), self._refrescar_empleados(), self._refrescar_registros()))

    def _crear_proyecto(self) -> None:
        def accion() -> None:
            proyecto = ecotech.Proyecto(self._numero(self.proy_id, "ID"), self.proy_nombre.get(), self.proy_descripcion.get(), date.today(), self.proy_estado.get())
            ecotech.crear_proyecto(self.conexion, proyecto)
            self._refrescar_proyectos()
        self._ejecutar(accion)

    def _actualizar_proyecto(self) -> None:
        self._ejecutar(lambda: (ecotech.actualizar_proyecto(self.conexion, self._numero(self.proy_id, "ID"), self.proy_estado.get()), self._refrescar_proyectos()))

    def _eliminar_proyecto(self) -> None:
        self._ejecutar(lambda: (ecotech.eliminar_proyecto(self.conexion, self._numero(self.proy_id, "ID")), self._refrescar_proyectos(), self._refrescar_registros()))

    def _crear_registro(self) -> None:
        def accion() -> None:
            empleado_id = self._numero(self.reg_empleado, "ID empleado")
            proyecto_id = self._numero(self.reg_proyecto, "ID proyecto")
            empleado_row = self.conexion.execute("SELECT * FROM usuario WHERE id = ?", (empleado_id,)).fetchone()
            proyecto_row = self.conexion.execute("SELECT * FROM proyecto WHERE id_proyecto = ?", (proyecto_id,)).fetchone()
            if empleado_row is None or proyecto_row is None:
                raise ValueError("El empleado y el proyecto deben existir.")
            empleado = ecotech.Empleado(empleado_id, empleado_row["nombre"], empleado_row["correo"], "", "", 0, empleado_row["id"] and date.today())
            proyecto = ecotech.Proyecto(proyecto_id, proyecto_row["nombre"], proyecto_row["descripcion"], proyecto_row["fecha_inicio"], proyecto_row["estado"])
            registro = ecotech.RegistroTiempo(self._numero(self.reg_id, "ID"), self.reg_fecha.get(), self.reg_horas.get(), self.reg_descripcion.get(), empleado, proyecto)
            ecotech.crear_registro_tiempo(self.conexion, registro)
            self._refrescar_registros()
        self._ejecutar(accion)

    def _actualizar_registro(self) -> None:
        self._ejecutar(lambda: (ecotech.actualizar_registro_tiempo(self.conexion, self._numero(self.reg_id, "ID"), self.reg_horas.get()), self._refrescar_registros()))

    def _eliminar_registro(self) -> None:
        self._ejecutar(lambda: (ecotech.eliminar_registro_tiempo(self.conexion, self._numero(self.reg_id, "ID")), self._refrescar_registros()))

    @staticmethod
    def _llenar(tabla: ttk.Treeview, filas: list[sqlite3.Row], valores) -> None:
        """Reemplaza el contenido visible de una tabla."""
        tabla.delete(*tabla.get_children())
        for fila in filas:
            tabla.insert("", "end", values=valores(fila))

    def _refrescar_departamentos(self) -> None:
        self._llenar(self.tabla_dept, ecotech.consultar_departamentos(self.conexion), lambda f: (f["id_dept"], f["nombre_dept"], f["gerente_id"]))

    def _refrescar_empleados(self) -> None:
        self._llenar(self.tabla_emp, ecotech.consultar_empleados(self.conexion), lambda f: (f["id"], f["nombre"], f["correo"], f["salario"], f["id_departamento"]))

    def _refrescar_proyectos(self) -> None:
        self._llenar(self.tabla_proy, ecotech.consultar_proyectos(self.conexion), lambda f: (f["id_proyecto"], f["nombre"], f["descripcion"], f["estado"]))

    def _refrescar_registros(self) -> None:
        self._llenar(self.tabla_reg, ecotech.consultar_registros_tiempo(self.conexion), lambda f: (f["id_registro"], f["fecha"], f["horas"], f["descripcion"], f["empleado_id"], f["proyecto_id"]))

    def _cerrar(self) -> None:
        """Cierra la conexion y la ventana de forma segura."""
        self.conexion.close()
        self.destroy()


if __name__ == "__main__":
    EcoTechApp().mainloop()