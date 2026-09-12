"""Sistema de gestion empresarial de EcoTech Solutions.

La estructura del dominio sigue el diagrama UML entregado: Usuario es la
abstraccion comun de Empleado y Administrador; Departamento agrega empleados;
Empleado y Proyecto se asocian de muchos a muchos; y RegistroTiempo vincula a
un empleado con un proyecto.

La persistencia usa exclusivamente sqlite3, incluida en la biblioteca estandar
de Python. Las funciones CRUD estan separadas de las entidades para conservar
la correspondencia entre el modelo UML y la infraestructura de datos.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Optional


def _decimal_positivo(valor: Decimal | int | float | str) -> Decimal:
    """Convierte un valor a Decimal y exige que no sea negativo."""
    try:
        resultado = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("El valor debe ser numerico.") from error
    if resultado < 0:
        raise ValueError("El valor no puede ser negativo.")
    return resultado


def _fecha_valida(valor: date | str) -> date:
    """Convierte una fecha ISO a date y captura entradas mal formadas."""
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError) as error:
        raise ValueError("La fecha debe tener formato AAAA-MM-DD.") from error


class Usuario(ABC):
    """Clase abstracta UML que centraliza identidad y acceso del sistema."""

    def __init__(self, id: int, nombre: str, correo: str) -> None:
        """Construye la identidad comun a Empleado y Administrador."""
        if not isinstance(id, int) or id <= 0:
            raise ValueError("id debe ser un entero positivo.")
        if not nombre.strip() or "@" not in correo:
            raise ValueError("Nombre y correo deben ser validos.")
        self._id = id
        self._nombre = nombre.strip()
        self._correo = correo.strip()

    @property
    def id(self) -> int:
        """Devuelve el identificador encapsulado del usuario."""
        return self._id

    @property
    def nombre(self) -> str:
        """Devuelve el nombre encapsulado del usuario."""
        return self._nombre

    @property
    def correo(self) -> str:
        """Devuelve el correo encapsulado del usuario."""
        return self._correo

    @abstractmethod
    def puede_acceder(self, modulo: str) -> bool:
        """Define el contrato UML de autorizacion para cada tipo de usuario."""
        raise NotImplementedError


class Empleado(Usuario):
    """Empleado UML: hereda identidad de Usuario y registra trabajo."""

    def __init__(
        self,
        id: int,
        nombre: str,
        correo: str,
        direccion: str,
        telefono: str,
        salario: Decimal | int | float | str,
        fecha_inicio: date | str,
        id_departamento: Optional[int] = None,
    ) -> None:
        """Construye los atributos privados definidos para Empleado."""
        super().__init__(id, nombre, correo)
        self._direccion = direccion.strip()
        self._telefono = telefono.strip()
        self._salario = _decimal_positivo(salario)
        self._fecha_inicio = _fecha_valida(fecha_inicio)
        self._id_departamento = id_departamento
        self._proyectos: list[Proyecto] = []
        self._registros: list[RegistroTiempo] = []

    def puede_acceder(self, modulo: str) -> bool:
        """Permite al empleado acceder a modulos operativos autorizados."""
        return modulo.strip().lower() in {"proyectos", "horas", "perfil"}

    def get_salario(self) -> Decimal:
        """Devuelve el salario, respetando el acceso controlado del UML."""
        return self._salario

    def set_salario(self, v: Decimal | int | float | str) -> bool:
        """Valida y actualiza salario; ValueError protege datos invalidos."""
        self._salario = _decimal_positivo(v)
        return True

    def registrar_horas(
        self,
        fecha: date | str | None = None,
        horas: Decimal | int | float | str = 0,
        descripcion: str = "",
        proyecto: Optional[Proyecto] = None,
    ) -> RegistroTiempo:
        """Crea un RegistroTiempo y mantiene la asociacion Empleado-registro.

        El UML muestra el metodo sin parametros; los parametros opcionales
        permiten que la operacion sea util en una implementacion ejecutable.
        """
        registro = RegistroTiempo(
            id_registro=len(self._registros) + 1,
            fecha=fecha or date.today(),
            horas=horas,
            descripcion=descripcion,
            empleado=self,
            proyecto=proyecto,
        )
        self._registros.append(registro)
        if proyecto is not None:
            proyecto._registros.append(registro)
        return registro

    def obtener_proyectos(self) -> list[Proyecto]:
        """Devuelve los proyectos asociados sin exponer la lista interna."""
        return list(self._proyectos)


class Administrador(Usuario):
    """Administrador UML: usuario funcional con permisos de gestion."""

    def puede_acceder(self, modulo: str) -> bool:
        """Permite al administrador acceder a cualquier modulo registrado."""
        return bool(modulo.strip())

    def crear_departamento(
        self,
        id_dept: int = 1,
        nombre_dept: str = "Nuevo departamento",
        gerente: Optional[Empleado] = None,
    ) -> Departamento:
        """Crea un Departamento; el rol no requiere atributos propios."""
        return Departamento(id_dept, nombre_dept, gerente)

    def generar_informe(self, contenido: str = "") -> str:
        """Genera el texto base de un informe administrativo."""
        return contenido or "Informe generado por Administrador"


class Departamento:
    """Departamento UML que agrega empleados sin poseer su ciclo de vida."""

    def __init__(
        self, id_dept: int, nombre_dept: str, gerente: Optional[Empleado] = None
    ) -> None:
        """Construye un departamento con una coleccion de referencias."""
        if id_dept <= 0 or not nombre_dept.strip():
            raise ValueError("Departamento invalido.")
        self._id_dept = id_dept
        self._nombre_dept = nombre_dept.strip()
        self._gerente = gerente
        self._empleados: list[Empleado] = []

    def agregar_empleado(self, e: Empleado) -> bool:
        """Agrega una referencia de empleado y sincroniza su departamento."""
        if not isinstance(e, Empleado):
            raise ValueError("Solo se pueden agregar empleados.")
        if e not in self._empleados:
            self._empleados.append(e)
            e._id_departamento = self._id_dept
        return True

    def remover_empleado(self, e: Empleado) -> bool:
        """Remueve la referencia sin destruir la instancia de Empleado."""
        if e in self._empleados:
            self._empleados.remove(e)
            e._id_departamento = None
            return True
        return False

    def listar_empleados(self) -> list[Empleado]:
        """Devuelve una copia de los empleados agregados."""
        return list(self._empleados)


class Proyecto:
    """Proyecto UML asignable a cero o mas empleados."""

    def __init__(
        self,
        id_proyecto: int,
        nombre: str,
        descripcion: str,
        fecha_inicio: date | str,
        estado: str,
    ) -> None:
        """Construye los datos del proyecto y sus asociaciones en memoria."""
        if id_proyecto <= 0 or not nombre.strip() or not estado.strip():
            raise ValueError("Proyecto invalido.")
        self._id_proyecto = id_proyecto
        self._nombre = nombre.strip()
        self._descripcion = descripcion.strip()
        self._fecha_inicio = _fecha_valida(fecha_inicio)
        self._estado = estado.strip()
        self._empleados: list[Empleado] = []
        self._registros: list[RegistroTiempo] = []

    def asignar_empleado(self, e: Empleado) -> bool:
        """Crea la asociacion muchos a muchos Empleado-Proyecto."""
        if not isinstance(e, Empleado):
            raise ValueError("Solo se pueden asignar empleados.")
        if e not in self._empleados:
            self._empleados.append(e)
            e._proyectos.append(self)
        return True

    def remover_empleado(self, e: Empleado) -> bool:
        """Elimina la asociacion sin eliminar ninguna de las entidades."""
        if e in self._empleados:
            self._empleados.remove(e)
            if self in e._proyectos:
                e._proyectos.remove(self)
            return True
        return False

    def calcular_total_horas(self) -> Decimal:
        """Suma las horas de registros que pertenecen a este proyecto."""
        return sum((registro.horas for registro in self._registros), Decimal("0"))


class RegistroTiempo:
    """RegistroTiempo UML que pertenece a un proyecto y a un empleado."""

    def __init__(
        self,
        id_registro: int,
        fecha: date | str,
        horas: Decimal | int | float | str,
        descripcion: str,
        empleado: Optional[Empleado] = None,
        proyecto: Optional[Proyecto] = None,
    ) -> None:
        """Construye un registro validando fecha y limite diario de horas."""
        if id_registro <= 0 or not descripcion.strip():
            raise ValueError("Registro de tiempo invalido.")
        self._id_registro = id_registro
        self._fecha = _fecha_valida(fecha)
        self._horas = _decimal_positivo(horas)
        self._descripcion = descripcion.strip()
        self._empleado = empleado
        self._proyecto = proyecto
        self.validar_limite_diario()

    @property
    def horas(self) -> Decimal:
        """Devuelve las horas encapsuladas del registro."""
        return self._horas

    def validar_limite_diario(self) -> bool:
        """Exige entre cero y veinticuatro horas para un dia."""
        if self._horas > Decimal("24"):
            raise ValueError("Un registro no puede superar 24 horas diarias.")
        return True

    def obtener_resumen(self) -> str:
        """Devuelve un resumen legible del registro de tiempo."""
        return f"{self._fecha.isoformat()}: {self._horas} h - {self._descripcion}"


class ReporteManager:
    """Servicio UML para generar y exportar reportes."""

    def __init__(
        self,
        id_reporte: int,
        tipo: str,
        fecha_generacion: date | str,
    ) -> None:
        """Construye los metadatos privados del reporte."""
        if id_reporte <= 0 or not tipo.strip():
            raise ValueError("Reporte invalido.")
        self._id_reporte = id_reporte
        self._tipo = tipo.strip()
        self._fecha_generacion = _fecha_valida(fecha_generacion)

    def generar_reporte_empleado(self, emp: Empleado) -> str:
        """Genera un reporte textual a partir de un empleado."""
        if not isinstance(emp, Empleado):
            raise ValueError("Se requiere un Empleado.")
        horas = sum((r.horas for r in emp._registros), Decimal("0"))
        return f"Empleado: {emp.nombre}\nHoras registradas: {horas}"

    def exportar_pdf(self, contenido: str, ruta: str) -> bool:
        """Escribe texto con extension PDF; la exportacion real requiere una libreria PDF."""
        try:
            Path(ruta).write_text(contenido, encoding="utf-8")
            return True
        except (OSError, TypeError) as error:
            raise ValueError(f"No se pudo exportar el reporte: {error}") from error

    def exportar_excel(self, datos: Any, ruta: str) -> bool:
        """Escribe una representacion tabular simple sin dependencia externa."""
        try:
            filas = datos if isinstance(datos, Iterable) and not isinstance(datos, str) else [datos]
            Path(ruta).write_text("\n".join(str(fila) for fila in filas), encoding="utf-8")
            return True
        except (OSError, TypeError) as error:
            raise ValueError(f"No se pudo exportar el reporte: {error}") from error


def inicializar_bd(ruta: str | Path = ":memory:") -> sqlite3.Connection:
    """Crea la conexion y el esquema SQLite con claves foraneas activas.

    La configuracion usa sqlite3.connect(ruta), activa foreign_keys y crea una
    tabla por entidad persistible mas la tabla intermedia de la asociacion N:N.
    CREATE TABLE IF NOT EXISTS hace segura la inicializacion repetida.
    """
    try:
        conexion = sqlite3.connect(str(ruta))
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS empleado (
                id INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE,
                direccion TEXT NOT NULL,
                telefono TEXT NOT NULL,
                salario NUMERIC NOT NULL CHECK (salario >= 0),
                fecha_inicio TEXT NOT NULL,
                id_departamento INTEGER REFERENCES departamento(id_dept) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS administrador (
                id INTEGER PRIMARY KEY REFERENCES usuario(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS departamento (
                id_dept INTEGER PRIMARY KEY,
                nombre_dept TEXT NOT NULL,
                gerente_id INTEGER REFERENCES empleado(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS proyecto (
                id_proyecto INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                estado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS registro_tiempo (
                id_registro INTEGER PRIMARY KEY,
                fecha TEXT NOT NULL,
                horas NUMERIC NOT NULL CHECK (horas >= 0 AND horas <= 24),
                descripcion TEXT NOT NULL,
                empleado_id INTEGER NOT NULL REFERENCES empleado(id) ON DELETE CASCADE,
                proyecto_id INTEGER NOT NULL REFERENCES proyecto(id_proyecto) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS empleado_proyecto (
                empleado_id INTEGER NOT NULL REFERENCES empleado(id) ON DELETE CASCADE,
                proyecto_id INTEGER NOT NULL REFERENCES proyecto(id_proyecto) ON DELETE CASCADE,
                PRIMARY KEY (empleado_id, proyecto_id)
            );
            """
        )
        conexion.commit()
        return conexion
    except sqlite3.Error:
        if "conexion" in locals():
            conexion.close()
        raise


def crear_empleado(conexion: sqlite3.Connection, empleado: Empleado) -> bool:
    """CRUD CREATE de Empleado y su identidad Usuario en una transaccion."""
    try:
        conexion.execute(
            "INSERT INTO usuario(id, nombre, correo) VALUES (?, ?, ?)",
            (empleado.id, empleado.nombre, empleado.correo),
        )
        conexion.execute(
            """INSERT INTO empleado
            (id, direccion, telefono, salario, fecha_inicio, id_departamento)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                empleado.id,
                empleado._direccion,
                empleado._telefono,
                str(empleado.get_salario()),
                empleado._fecha_inicio.isoformat(),
                empleado._id_departamento,
            ),
        )
        conexion.commit()
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def consultar_empleados(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    """CRUD READ de todos los empleados con datos de Usuario."""
    try:
        return list(conexion.execute("""SELECT u.id, u.nombre, u.correo,
            e.direccion, e.telefono, e.salario, e.fecha_inicio, e.id_departamento
            FROM usuario u JOIN empleado e ON e.id = u.id ORDER BY u.id"""))
    except sqlite3.Error:
        raise


def actualizar_empleado(
    conexion: sqlite3.Connection, empleado_id: int, salario: Decimal | int | float | str
) -> bool:
    """CRUD UPDATE del salario de un empleado validando el valor primero."""
    salario_valido = _decimal_positivo(salario)
    try:
        cursor = conexion.execute(
            "UPDATE empleado SET salario = ? WHERE id = ?",
            (str(salario_valido), empleado_id),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Empleado no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def eliminar_empleado(conexion: sqlite3.Connection, empleado_id: int) -> bool:
    """CRUD DELETE de Empleado; CASCADE elimina usuario y relaciones."""
    try:
        cursor = conexion.execute("DELETE FROM usuario WHERE id = ?", (empleado_id,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Empleado no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def crear_departamento(conexion: sqlite3.Connection, departamento: Departamento) -> bool:
    """CRUD CREATE de Departamento."""
    try:
        gerente_id = departamento._gerente.id if departamento._gerente else None
        conexion.execute(
            "INSERT INTO departamento(id_dept, nombre_dept, gerente_id) VALUES (?, ?, ?)",
            (departamento._id_dept, departamento._nombre_dept, gerente_id),
        )
        conexion.commit()
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def consultar_departamentos(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    """CRUD READ de Departamento."""
    try:
        return list(conexion.execute("SELECT * FROM departamento ORDER BY id_dept"))
    except sqlite3.Error:
        raise


def actualizar_departamento(
    conexion: sqlite3.Connection, id_dept: int, nombre_dept: str
) -> bool:
    """CRUD UPDATE del nombre de Departamento."""
    if not nombre_dept.strip():
        raise ValueError("El nombre del departamento es obligatorio.")
    try:
        cursor = conexion.execute(
            "UPDATE departamento SET nombre_dept = ? WHERE id_dept = ?",
            (nombre_dept.strip(), id_dept),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Departamento no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def eliminar_departamento(conexion: sqlite3.Connection, id_dept: int) -> bool:
    """CRUD DELETE de Departamento; sus empleados quedan sin departamento."""
    try:
        cursor = conexion.execute("DELETE FROM departamento WHERE id_dept = ?", (id_dept,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Departamento no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def crear_proyecto(conexion: sqlite3.Connection, proyecto: Proyecto) -> bool:
    """CRUD CREATE de Proyecto."""
    try:
        conexion.execute(
            "INSERT INTO proyecto VALUES (?, ?, ?, ?, ?)",
            (
                proyecto._id_proyecto,
                proyecto._nombre,
                proyecto._descripcion,
                proyecto._fecha_inicio.isoformat(),
                proyecto._estado,
            ),
        )
        conexion.commit()
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def consultar_proyectos(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    """CRUD READ de Proyecto."""
    try:
        return list(conexion.execute("SELECT * FROM proyecto ORDER BY id_proyecto"))
    except sqlite3.Error:
        raise


def actualizar_proyecto(
    conexion: sqlite3.Connection, id_proyecto: int, estado: str
) -> bool:
    """CRUD UPDATE del estado de Proyecto."""
    if not estado.strip():
        raise ValueError("El estado es obligatorio.")
    try:
        cursor = conexion.execute(
            "UPDATE proyecto SET estado = ? WHERE id_proyecto = ?",
            (estado.strip(), id_proyecto),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Proyecto no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def eliminar_proyecto(conexion: sqlite3.Connection, id_proyecto: int) -> bool:
    """CRUD DELETE de Proyecto y sus registros/asignaciones."""
    try:
        cursor = conexion.execute("DELETE FROM proyecto WHERE id_proyecto = ?", (id_proyecto,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Proyecto no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def crear_registro_tiempo(conexion: sqlite3.Connection, registro: RegistroTiempo) -> bool:
    """CRUD CREATE de RegistroTiempo con empleado y proyecto obligatorios."""
    if registro._empleado is None or registro._proyecto is None:
        raise ValueError("El registro requiere empleado y proyecto.")
    try:
        conexion.execute(
            """INSERT INTO registro_tiempo
            (id_registro, fecha, horas, descripcion, empleado_id, proyecto_id)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                registro._id_registro,
                registro._fecha.isoformat(),
                str(registro.horas),
                registro._descripcion,
                registro._empleado.id,
                registro._proyecto._id_proyecto,
            ),
        )
        conexion.commit()
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def consultar_registros_tiempo(conexion: sqlite3.Connection) -> list[sqlite3.Row]:
    """CRUD READ de RegistroTiempo."""
    try:
        return list(conexion.execute("SELECT * FROM registro_tiempo ORDER BY id_registro"))
    except sqlite3.Error:
        raise


def actualizar_registro_tiempo(
    conexion: sqlite3.Connection, id_registro: int, horas: Decimal | int | float | str
) -> bool:
    """CRUD UPDATE de horas de RegistroTiempo con limite diario."""
    horas_validas = _decimal_positivo(horas)
    if horas_validas > Decimal("24"):
        raise ValueError("Un registro no puede superar 24 horas diarias.")
    try:
        cursor = conexion.execute(
            "UPDATE registro_tiempo SET horas = ? WHERE id_registro = ?",
            (str(horas_validas), id_registro),
        )
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Registro no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def eliminar_registro_tiempo(conexion: sqlite3.Connection, id_registro: int) -> bool:
    """CRUD DELETE de RegistroTiempo."""
    try:
        cursor = conexion.execute("DELETE FROM registro_tiempo WHERE id_registro = ?", (id_registro,))
        conexion.commit()
        if cursor.rowcount == 0:
            raise ValueError("Registro no encontrado.")
        return True
    except sqlite3.Error:
        conexion.rollback()
        raise


def demo_crud() -> None:
    """Ejecuta una prueba pequena de las cuatro operaciones CRUD principales."""
    conexion = inicializar_bd()
    try:
        departamento = Departamento(1, "Ingenieria")
        empleado = Empleado(1, "Ana Perez", "ana@ecotech.test", "Calle 1", "555-0101", 2500, "2026-01-10")
        proyecto = Proyecto(1, "Plataforma verde", "Gestion energetica", "2026-02-01", "activo")
        departamento.agregar_empleado(empleado)
        proyecto.asignar_empleado(empleado)
        registro = empleado.registrar_horas("2026-02-02", 8, "Implementacion", proyecto)
        crear_departamento(conexion, departamento)
        crear_empleado(conexion, empleado)
        crear_proyecto(conexion, proyecto)
        crear_registro_tiempo(conexion, registro)
        actualizar_empleado(conexion, empleado.id, 2700)
        actualizar_departamento(conexion, departamento._id_dept, "Ingenieria y datos")
        actualizar_proyecto(conexion, proyecto._id_proyecto, "en_progreso")
        actualizar_registro_tiempo(conexion, registro._id_registro, 7.5)
        assert len(consultar_empleados(conexion)) == 1
        assert len(consultar_departamentos(conexion)) == 1
        assert len(consultar_proyectos(conexion)) == 1
        assert len(consultar_registros_tiempo(conexion)) == 1
        eliminar_registro_tiempo(conexion, registro._id_registro)
        eliminar_proyecto(conexion, proyecto._id_proyecto)
        eliminar_empleado(conexion, empleado.id)
        eliminar_departamento(conexion, departamento._id_dept)
        assert not consultar_empleados(conexion)
    finally:
        conexion.close()


# NOTAS PARA EVALUACIÓN CRÍTICA DE IA
# 1. Revisar si las reglas de acceso de Usuario coinciden con los permisos reales.
# 2. Confirmar el límite diario de 24 horas y las reglas de negocio de horas extra.
# 3. Validar si Administrador necesita atributos propios, como nivel de permisos.
# 4. Precisar las etiquetas y multiplicidades de las dependencias de ReporteManager.
# 5. Sustituir las exportaciones de texto por librerías PDF/Excel si el entregable lo exige.
# 6. Revisar autenticación, autorización, formato de correo y política de duplicados.
# 7. Añadir pruebas automatizadas y migraciones si la base de datos deja de ser temporal.


if __name__ == "__main__":
    demo_crud()
    print("Demostracion CRUD completada correctamente.")