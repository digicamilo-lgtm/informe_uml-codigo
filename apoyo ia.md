# Registro de apoyo de inteligencia artificial
## Sistema de gestión empresarial EcoTech Solutions

Este documento registra cuatro situaciones en las que se utilizó una herramienta de inteligencia artificial como apoyo durante el desarrollo del sistema. La IA se utilizó para proponer estructuras, explicar decisiones y ayudar a verificar la implementación. Las decisiones finales fueron revisadas y adaptadas al diagrama UML, al informe técnico y a los requerimientos del proyecto.

## Situación 1: Traducción del diagrama UML a clases Python

**Intervención de la IA:**

La IA ayudó a transformar las siete clases del diagrama UML en clases Python: `Usuario`, `Empleado`, `Administrador`, `Departamento`, `Proyecto`, `RegistroTiempo` y `ReporteManager`.

También propuso los constructores, atributos y métodos correspondientes al diagrama, respetando los nombres definidos en el modelo.

**Decisión tomada:**

La propuesta fue aceptada como base porque mantenía la correspondencia entre el UML y el código. Posteriormente se revisaron los nombres, tipos y responsabilidades de cada clase para evitar que se agregaran elementos que no estuvieran justificados por el diseño.

**Resultado:**

Se creó el modelo orientado a objetos en `ecotech.py`, incluyendo docstrings que explican la relación entre cada clase Python y su entidad UML.

## Situación 2: Implementación de herencia, abstracción y encapsulamiento

**Intervención de la IA:**

La IA sugirió implementar `Usuario` como una clase abstracta utilizando `ABC` y `abstractmethod`, haciendo que `Empleado` y `Administrador` heredaran de ella.

También recomendó usar atributos privados con prefijo `_`, propiedades de lectura y métodos de acceso controlado como `get_salario()` y `set_salario()`.

**Decisión tomada:**

La propuesta fue aceptada porque coincide con el informe técnico, que identifica a `Usuario` como clase abstracta y solicita aplicar encapsulamiento. Se mantuvo `puede_acceder()` como método abstracto para obligar a cada subclase a definir sus permisos.

La IA también señaló que `Administrador` no tenía atributos propios. Se decidió conservar la clase sin atributos adicionales, dejando documentado que podría incorporar un atributo como `nivel_permisos` en una versión futura.

**Resultado:**

El código evita la duplicación de `id`, `nombre` y `correo`, y protege el acceso directo a los datos internos de las entidades.

## Situación 3: Diseño de la base de datos y operaciones CRUD

**Intervención de la IA:**

La IA propuso utilizar `sqlite3`, crear una función `inicializar_bd()` y representar las relaciones del UML mediante tablas y claves foráneas.

También ayudó a estructurar las operaciones de creación, consulta, actualización y eliminación para `Empleado`, `Departamento`, `Proyecto` y `RegistroTiempo`.

Para la relación muchos a muchos entre empleados y proyectos, propuso la tabla intermedia `empleado_proyecto`.

**Decisión tomada:**

La propuesta fue aceptada porque `sqlite3` era un requisito explícito y porque las tablas reflejan las relaciones del modelo. Se añadieron claves primarias, claves foráneas, restricciones de valores y consultas parametrizadas.

La implementación fue probada mediante una demostración CRUD ejecutable, en la que se crean, consultan, actualizan y eliminan registros.

**Resultado:**

El sistema cuenta con persistencia local en `ecotech.db` y mantiene separadas las funciones de base de datos de las clases del dominio.

## Situación 4: Manejo de errores, validaciones e interfaz de usuario

**Intervención de la IA:**

La IA ayudó a identificar las validaciones necesarias para evitar datos incorrectos, como salarios negativos, fechas inválidas, identificadores no positivos y registros de más de 24 horas.

También propuso separar la interfaz de usuario de la lógica del sistema y crear `interfaz.py` con Tkinter. La interfaz contiene formularios, tablas y botones para realizar operaciones CRUD.

**Decisión tomada:**

La separación fue aceptada porque permite mantener `ecotech.py` como backend y `interfaz.py` como capa de presentación. Las excepciones se revisaron para utilizar tipos específicos como `ValueError`, `sqlite3.Error`, `OSError` y `TypeError`.

La exportación de PDF y Excel se dejó identificada como un punto que requiere revisión adicional, ya que una implementación completa necesitaría librerías especializadas.

**Resultado:**

El usuario puede interactuar con el sistema mediante una ventana gráfica, mientras que los errores se muestran mediante mensajes y no provocan el cierre inesperado de la aplicación.

## Conclusión crítica

La inteligencia artificial se utilizó como herramienta de apoyo para acelerar la traducción del diseño UML, proponer estructuras de código, organizar la persistencia y mejorar la interacción con el usuario. Sin embargo, las propuestas fueron revisadas de acuerdo con el UML y el informe técnico.

Las decisiones que requieren revisión manual son:

- Confirmar las reglas reales de permisos de cada tipo de usuario.
- Determinar si `Administrador` necesita atributos propios.
- Validar el límite de 24 horas según las reglas del negocio.
- Precisar las dependencias de `ReporteManager`.
- Integrar librerías reales para exportar archivos PDF y Excel.
- Incorporar pruebas automatizadas para ampliar la verificación del sistema.

Por tanto, la IA intervino como apoyo técnico, pero la aceptación, modificación y documentación de las propuestas se realizó considerando la coherencia del modelo, los requerimientos y las pruebas ejecutadas.
