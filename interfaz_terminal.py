"""Interfaz de terminal para operar EcoTech Solutions sin Tkinter."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
import getpass
import sqlite3
from typing import Callable

import ecotech


class InterfazTerminal:
    """Menu interactivo que reutiliza el modelo y el CRUD de ecotech."""

    def __init__(self, ruta_bd: str = "ecotech.db") -> None:
        self.conexion = ecotech.inicializar_bd(ruta_bd)

    def ejecutar(self) -> None:
        """Muestra el menu principal hasta que el usuario decide salir."""
        print("\nEcoTech Solutions - Interfaz de terminal")
        print(f"Base de datos: {self.conexion.execute('PRAGMA database_list').fetchone()[2]}")
        if not self._autenticar():
            print("No fue posible autenticar la sesion.")
            return
        while True:
            self._mostrar_menu(
                "MENU PRINCIPAL",
                [
                    ("1", "Departamentos"),
                    ("2", "Empleados"),
                    ("3", "Proyectos"),
                    ("4", "Registros de horas"),
                    ("5", "Servicios externos"),
                    ("0", "Salir"),
                ],
            )
            opcion = self._pedir("Selecciona una opcion: ")
            if opcion == "0":
                print("Sesion finalizada.")
                return
            acciones = {
                "1": self._menu_departamentos,
                "2": self._menu_empleados,
                "3": self._menu_proyectos,
                "4": self._menu_registros,
                "5": self._menu_servicios_externos,
            }
            self._ejecutar_opcion(acciones.get(opcion), "Opcion no valida.")

    def _autenticar(self) -> bool:
        """Solicita credenciales y permite crear el primer usuario local."""
        cantidad = self.conexion.execute("SELECT COUNT(*) FROM usuario_acceso").fetchone()[0]
        if cantidad == 0:
            print("No hay usuarios. Crea el primer usuario administrador.")
            nombre = self._pedir_obligatorio("Usuario: ")
            password = getpass.getpass("Contrasena (minimo 8 caracteres): ")
            confirmacion = getpass.getpass("Repite la contrasena: ")
            if password != confirmacion:
                print("Error: las contrasenas no coinciden.")
                return False
            ecotech.crear_usuario(self.conexion, nombre, password)
            print("Usuario creado. Sesion iniciada.")
            return True
        nombre = self._pedir_obligatorio("Usuario: ")
        password = getpass.getpass("Contrasena: ")
        if ecotech.autenticar_usuario(self.conexion, nombre, password):
            return True
        print("Credenciales invalidas.")
        return False

    def _menu_servicios_externos(self) -> None:
        """Permite consultar clima e indicadores y guardar sus respuestas."""
        self._mostrar_menu(
            "SERVICIOS EXTERNOS",
            [("1", "Clima actual"), ("2", "Indicador economico"), ("3", "Historial local"), ("0", "Volver")],
        )
        opcion = self._pedir("Selecciona una opcion: ")
        acciones = {"1": self._consultar_clima, "2": self._consultar_indicador, "3": self._listar_consultas_api}
        if opcion == "0":
            return
        self._ejecutar_opcion(acciones.get(opcion), "Opcion no valida.")

    def _consultar_clima(self) -> None:
        ciudad = self._pedir_obligatorio("Ciudad: ")
        resultado = ecotech.consultar_clima(ciudad)
        ecotech.guardar_consulta_api(self.conexion, "OpenWeather Ecotech", ciudad, resultado)
        print(
            f"{resultado['ciudad']}: {resultado['temperatura_c']} C, "
            f"{resultado['estado']}, humedad {resultado['humedad_porcentaje']}%."
        )

    def _consultar_indicador(self) -> None:
        indicador = self._pedir_obligatorio("Indicador (ejemplo: dolar): ")
        fecha = self._pedir("Fecha AAAA-MM-DD (Enter=hoy): ") or None
        resultado = ecotech.consultar_indicador(indicador, fecha)
        ecotech.guardar_consulta_api(self.conexion, "mindicador.cl", indicador, resultado)
        print(
            f"{resultado['indicador']}: {resultado['valor']} {resultado['unidad']} "
            f"({resultado['fecha']})."
        )

    def _listar_consultas_api(self) -> None:
        self._imprimir_filas(
            ecotech.listar_consultas_api(self.conexion),
            ["id", "servicio", "consulta", "respuesta_json", "fecha"],
        )

    def _menu_departamentos(self) -> None:
        self._menu_crud(
            "DEPARTAMENTOS",
            self._listar_departamentos,
            {
                "2": self._crear_departamento,
                "3": self._actualizar_departamento,
                "4": self._eliminar_departamento,
            },
        )

    def _menu_empleados(self) -> None:
        self._menu_crud(
            "EMPLEADOS",
            self._listar_empleados,
            {
                "2": self._crear_empleado,
                "3": self._actualizar_empleado,
                "4": self._eliminar_empleado,
            },
        )

    def _menu_proyectos(self) -> None:
        self._menu_crud(
            "PROYECTOS",
            self._listar_proyectos,
            {
                "2": self._crear_proyecto,
                "3": self._actualizar_proyecto,
                "4": self._eliminar_proyecto,
                "5": self._asignar_empleado,
                "6": self._desasignar_empleado,
                "7": self._listar_asignaciones,
            },
            [("5", "Asignar empleado"), ("6", "Desasignar empleado"), ("7", "Listar asignaciones")],
        )

    def _menu_registros(self) -> None:
        self._menu_crud(
            "REGISTROS DE HORAS",
            self._listar_registros,
            {
                "2": self._crear_registro,
                "3": self._actualizar_registro,
                "4": self._eliminar_registro,
            },
        )

    def _menu_crud(
        self,
        titulo: str,
        listar: Callable[[], None],
        acciones: dict[str, Callable[[], None]],
        opciones_extra: list[tuple[str, str]] | None = None,
    ) -> None:
        while True:
            opciones = [("1", "Listar"), ("2", "Crear"), ("3", "Actualizar"), ("4", "Eliminar")]
            opciones.extend(opciones_extra or [])
            opciones.append(("0", "Volver"))
            self._mostrar_menu(
                titulo,
                opciones,
            )
            opcion = self._pedir("Selecciona una opcion: ")
            if opcion == "0":
                return
            if opcion == "1":
                self._ejecutar_accion(listar)
            elif opcion in acciones:
                self._ejecutar_accion(acciones[opcion])
            else:
                print("Opcion no valida.")

    def _crear_departamento(self) -> None:
        id_dept = self._pedir_entero("ID del departamento: ")
        nombre = self._pedir_nombre_departamento()
        ecotech.crear_departamento(self.conexion, ecotech.Departamento(id_dept, nombre))
        print("Departamento creado.")

    def _actualizar_departamento(self) -> None:
        id_dept = self._pedir_id_existente(
            "ID del departamento (0/cancelar para salir): ",
            "departamento",
            "SELECT id_dept FROM departamento WHERE id_dept = ?",
        )
        if id_dept is None:
            return
        actual = self.conexion.execute(
            "SELECT nombre_dept FROM departamento WHERE id_dept = ?", (id_dept,)
        ).fetchone()["nombre_dept"]
        nombre = self._pedir_nombre_actualizable(
            "Nuevo nombre", actual, self._es_nombre_departamento
        )
        ecotech.actualizar_departamento(self.conexion, id_dept, nombre)
        print("Departamento actualizado.")

    def _eliminar_departamento(self) -> None:
        id_dept = self._pedir_entero("ID del departamento: ")
        ecotech.eliminar_departamento(self.conexion, id_dept)
        print("Departamento eliminado.")

    def _crear_empleado(self) -> None:
        empleado = ecotech.Empleado(
            self._pedir_entero("ID: "),
            self._pedir_nombre_persona(),
            self._pedir_correo(),
            self._pedir("Direccion: "),
            self._pedir("Telefono: "),
            self._pedir_numero("Salario", "ejemplo: 2500.50"),
            self._pedir_fecha("Fecha de inicio (AAAA-MM-DD, Enter=hoy): ", permitir_vacio=True),
            self._pedir_entero("ID de departamento (Enter=ninguno): ", permitir_vacio=True),
        )
        ecotech.crear_empleado(self.conexion, empleado)
        print("Empleado creado.")

    def _actualizar_empleado(self) -> None:
        empleado_id = self._pedir_id_existente(
            "ID del empleado (0/cancelar para salir): ",
            "empleado",
            "SELECT id FROM empleado WHERE id = ?",
        )
        if empleado_id is None:
            return
        salario = self._pedir_numero("Nuevo salario", "ejemplo: 2500.50")
        ecotech.actualizar_empleado(self.conexion, empleado_id, salario)
        print("Empleado actualizado.")

    def _eliminar_empleado(self) -> None:
        empleado_id = self._pedir_entero("ID del empleado: ")
        ecotech.eliminar_empleado(self.conexion, empleado_id)
        print("Empleado eliminado.")

    def _crear_proyecto(self) -> None:
        proyecto = ecotech.Proyecto(
            self._pedir_entero("ID: "),
            self._pedir_nombre_persona(),
            self._pedir_obligatorio("Descripcion: "),
            self._pedir_fecha("Fecha de inicio (AAAA-MM-DD, Enter=hoy): ", permitir_vacio=True),
            self._pedir_estado("Estado"),
        )
        ecotech.crear_proyecto(self.conexion, proyecto)
        print("Proyecto creado.")

    def _actualizar_proyecto(self) -> None:
        proyecto_id = self._pedir_id_existente(
            "ID del proyecto (0/cancelar para salir): ",
            "proyecto",
            "SELECT id_proyecto FROM proyecto WHERE id_proyecto = ?",
        )
        if proyecto_id is None:
            return
        estado = self._pedir_estado("Nuevo estado")
        ecotech.actualizar_proyecto(self.conexion, proyecto_id, estado)
        print("Proyecto actualizado.")

    def _eliminar_proyecto(self) -> None:
        proyecto_id = self._pedir_entero("ID del proyecto: ")
        ecotech.eliminar_proyecto(self.conexion, proyecto_id)
        print("Proyecto eliminado.")

    def _asignar_empleado(self) -> None:
        empleado_id = self._pedir_entero("ID del empleado: ")
        proyecto_id = self._pedir_entero("ID del proyecto: ")
        ecotech.asignar_empleado_proyecto(self.conexion, empleado_id, proyecto_id)
        print("Empleado asignado al proyecto.")

    def _desasignar_empleado(self) -> None:
        empleado_id = self._pedir_entero("ID del empleado: ")
        proyecto_id = self._pedir_entero("ID del proyecto: ")
        ecotech.desasignar_empleado_proyecto(self.conexion, empleado_id, proyecto_id)
        print("Empleado desasignado del proyecto.")

    def _listar_asignaciones(self) -> None:
        self._imprimir_filas(
            ecotech.consultar_asignaciones(self.conexion),
            ["empleado_id", "empleado", "proyecto_id", "proyecto"],
        )

    def _crear_registro(self) -> None:
        empleado_id = self._pedir_entero("ID del empleado: ")
        proyecto_id = self._pedir_entero("ID del proyecto: ")
        empleado_row = self.conexion.execute(
            "SELECT * FROM usuario WHERE id = ?", (empleado_id,)
        ).fetchone()
        proyecto_row = self.conexion.execute(
            "SELECT * FROM proyecto WHERE id_proyecto = ?", (proyecto_id,)
        ).fetchone()
        if empleado_row is None or proyecto_row is None:
            raise ValueError("El empleado y el proyecto deben existir.")
        empleado = ecotech.Empleado(
            empleado_id,
            empleado_row["nombre"],
            empleado_row["correo"],
            "",
            "",
            0,
            date.today(),
        )
        proyecto = ecotech.Proyecto(
            proyecto_id,
            proyecto_row["nombre"],
            proyecto_row["descripcion"],
            proyecto_row["fecha_inicio"],
            proyecto_row["estado"],
        )
        registro = ecotech.RegistroTiempo(
            self._pedir_entero("ID del registro: "),
            self._pedir_fecha("Fecha (AAAA-MM-DD, Enter=hoy): ", permitir_vacio=True),
            self._pedir_horas(),
            self._pedir_obligatorio("Descripcion: "),
            empleado,
            proyecto,
        )
        ecotech.crear_registro_tiempo(self.conexion, registro)
        print("Registro creado.")

    def _actualizar_registro(self) -> None:
        registro_id = self._pedir_id_existente(
            "ID del registro (0/cancelar para salir): ",
            "registro de horas",
            "SELECT id_registro FROM registro_tiempo WHERE id_registro = ?",
        )
        if registro_id is None:
            return
        horas = self._pedir_horas("Nuevas horas")
        ecotech.actualizar_registro_tiempo(self.conexion, registro_id, horas)
        print("Registro actualizado.")

    def _eliminar_registro(self) -> None:
        registro_id = self._pedir_entero("ID del registro: ")
        ecotech.eliminar_registro_tiempo(self.conexion, registro_id)
        print("Registro eliminado.")

    def _listar_departamentos(self) -> None:
        self._imprimir_filas(
            ecotech.consultar_departamentos(self.conexion),
            ["id_dept", "nombre_dept", "gerente_id"],
        )

    def _listar_empleados(self) -> None:
        self._imprimir_filas(
            ecotech.consultar_empleados(self.conexion),
            ["id", "nombre", "correo", "salario", "id_departamento"],
        )

    def _listar_proyectos(self) -> None:
        self._imprimir_filas(
            ecotech.consultar_proyectos(self.conexion),
            ["id_proyecto", "nombre", "descripcion", "fecha_inicio", "estado"],
        )

    def _listar_registros(self) -> None:
        self._imprimir_filas(
            ecotech.consultar_registros_tiempo(self.conexion),
            ["id_registro", "fecha", "horas", "descripcion", "empleado_id", "proyecto_id"],
        )

    @staticmethod
    def _mostrar_menu(titulo: str, opciones: list[tuple[str, str]]) -> None:
        print(f"\n--- {titulo} ---")
        for clave, texto in opciones:
            print(f"{clave}. {texto}")

    @staticmethod
    def _pedir(mensaje: str) -> str:
        try:
            return input(mensaje).strip()
        except EOFError as error:
            raise SystemExit("\nEntrada finalizada.") from error

    def _pedir_obligatorio(self, mensaje: str, ejemplo: str = "ejemplo: texto valido") -> str:
        while True:
            valor = self._pedir(mensaje)
            if valor:
                return valor
            print(f"Error: este campo es obligatorio; {ejemplo}.")

    @staticmethod
    def _es_nombre_persona(valor: str) -> bool:
        return bool(valor) and all(caracter.isalpha() or caracter.isspace() for caracter in valor)

    @staticmethod
    def _es_nombre_departamento(valor: str) -> bool:
        return bool(valor) and all(
            caracter.isalnum() or caracter.isspace() or caracter == "&"
            for caracter in valor
        )

    def _pedir_nombre_persona(self) -> str:
        while True:
            valor = self._pedir("Nombre: ")
            if self._es_nombre_persona(valor):
                return valor
            print(
                "Error: el nombre solo admite letras y espacios; ejemplo: Maria Gonzalez. "
                "No uses numeros ni simbolos."
            )

    def _pedir_nombre_departamento(self) -> str:
        while True:
            valor = self._pedir("Nombre del departamento: ")
            if self._es_nombre_departamento(valor):
                return valor
            print(
                "Error: el departamento admite letras, numeros, espacios y '&'; "
                "ejemplo: Departamento 4 o R&D 01."
            )

    def _pedir_nombre_actualizable(
        self, campo: str, actual: str, validador: Callable[[str], bool]
    ) -> str:
        while True:
            valor = self._pedir(f"{campo} [Enter={actual}]: ")
            if not valor:
                return actual
            if validador(valor):
                return valor
            print(
                "Error: el valor no tiene el formato permitido; "
                "pulsa Enter para conservarlo o escribe un valor valido."
            )

    def _pedir_id_existente(self, mensaje: str, entidad: str, consulta: str) -> int | None:
        while True:
            valor = self._pedir(mensaje)
            if valor.lower() in {"0", "cancelar"}:
                print(f"Actualizacion de {entidad} cancelada.")
                return None
            try:
                identificador = int(valor)
            except ValueError:
                print("Error: escribe un ID entero positivo; ejemplo: 12, o 0/cancelar para salir.")
                continue
            if identificador <= 0:
                print("Error: el ID debe ser positivo; escribe 0 o cancelar para salir.")
                continue
            existe = self.conexion.execute(consulta, (identificador,)).fetchone()
            if existe is not None:
                return identificador
            decision = self._pedir(
                f"Error: no existe ese {entidad}. Pulsa Enter para intentar otro ID "
                "o escribe 0/cancelar para volver: "
            )
            if decision.lower() in {"0", "cancelar"}:
                print(f"Actualizacion de {entidad} cancelada.")
                return None

    def _pedir_correo(self) -> str:
        while True:
            valor = self._pedir("Correo: ")
            if valor and "@" in valor and "." in valor.rsplit("@", 1)[-1]:
                return valor
            print("Error: escribe un correo valido con @ y dominio; ejemplo: ana@ecotech.com.")

    def _pedir_entero(self, mensaje: str, permitir_vacio: bool = False) -> int | None:
        while True:
            valor = self._pedir(mensaje)
            if permitir_vacio and not valor:
                return None
            try:
                resultado = int(valor)
            except ValueError:
                print("Error: debes escribir un numero entero, por ejemplo: 12.")
                continue
            if resultado <= 0:
                print("Error: el entero debe ser positivo, por ejemplo: 12.")
                continue
            return resultado

    def _pedir_numero(self, campo: str, ejemplo: str) -> Decimal:
        while True:
            valor = self._pedir(f"{campo}: ")
            try:
                resultado = Decimal(valor)
            except InvalidOperation:
                print(f"Error: {campo} debe ser numerico; {ejemplo}.")
                continue
            if not resultado.is_finite():
                print(f"Error: {campo} debe ser un numero finito; {ejemplo}.")
                continue
            if resultado < 0:
                print(f"Error: {campo} no puede ser negativo; {ejemplo}.")
                continue
            return resultado

    def _pedir_horas(self, campo: str = "Horas") -> Decimal:
        while True:
            horas = self._pedir_numero(campo, "ejemplo: 7.5")
            if horas > 24:
                print("Error: las horas deben estar entre 0 y 24; ejemplo: 7.5.")
                continue
            return horas

    def _pedir_estado(self, campo: str) -> str:
        estados = ("Planificacion", "En progreso", "Completado", "Cancelado")
        while True:
            print("Opciones de estado: 1. Planificacion  2. En progreso  3. Completado  4. Cancelado")
            valor = self._pedir(f"{campo} (1-4): ")
            try:
                indice = int(valor)
            except ValueError:
                print("Error: selecciona un estado escribiendo un numero del 1 al 4; ejemplo: 2.")
                continue
            if 1 <= indice <= len(estados):
                return estados[indice - 1]
            print("Error: la opcion debe estar entre 1 y 4; ejemplo: 2 para En progreso.")

    def _pedir_fecha(self, mensaje: str, permitir_vacio: bool = False) -> date | str:
        while True:
            valor = self._pedir(mensaje)
            if permitir_vacio and not valor:
                return date.today()
            try:
                return date.fromisoformat(valor)
            except ValueError:
                print(
                    "Error: escribe una fecha real con formato AAAA-MM-DD; "
                    "ejemplo: 2024-05-20."
                )

    def _ejecutar_opcion(self, accion: Callable[[], None] | None, mensaje: str) -> None:
        if accion is None:
            print(mensaje)
            return
        self._ejecutar_accion(accion)

    @staticmethod
    def _ejecutar_accion(accion: Callable[[], None]) -> None:
        try:
            accion()
        except (ValueError, sqlite3.Error, ecotech.ServicioExternoError) as error:
            print(f"Error: {error}")

    @staticmethod
    def _imprimir_filas(filas: list[sqlite3.Row], columnas: list[str]) -> None:
        if not filas:
            print("No hay registros.")
            return
        datos = [[str(fila[columna]) if fila[columna] is not None else "-" for columna in columnas] for fila in filas]
        anchos = [max(len(columna), *(len(fila[indice]) for fila in datos)) for indice, columna in enumerate(columnas)]
        separador = "-+-".join("-" * ancho for ancho in anchos)
        print(" | ".join(columna.upper().ljust(anchos[indice]) for indice, columna in enumerate(columnas)))
        print(separador)
        for fila in datos:
            print(" | ".join(valor.ljust(anchos[indice]) for indice, valor in enumerate(fila)))

    def cerrar(self) -> None:
        self.conexion.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Interfaz de terminal de EcoTech Solutions")
    parser.add_argument("--db", default="ecotech.db", help="Ruta del archivo SQLite")
    args = parser.parse_args()
    interfaz = InterfazTerminal(args.db)
    try:
        interfaz.ejecutar()
    finally:
        interfaz.cerrar()


if __name__ == "__main__":
    main()
