# Rich Argparse Markup Guide

Este documento explica cómo usar el markup de Rich en las descripciones de comandos de `wine-chroot`.

## Markup Básico Soportado

Rich-argparse soporta **console markup** directamente en las strings de ayuda. Los estilos se aplican usando corchetes:

### Estilos de Texto

```python
"[bold]texto en negritas[/bold]"
"[italic]texto en itálicas[/italic]"  # o usar [i]...[/i]
"[bold italic]negritas e itálicas[/bold italic]"
"[underline]subrayado[/underline]"  # o usar [u]...[/u]
"[dim]texto atenuado[/dim]"
"[strike]tachado[/strike]"  # o usar [s]...[/s]
```

### Colores

```python
# Colores básicos
"[red]rojo[/red]"
"[green]verde[/green]"
"[blue]azul[/blue]"
"[yellow]amarillo[/yellow]"
"[magenta]magenta[/magenta]"
"[cyan]cyan[/cyan]"
"[white]blanco[/white]"

# Colores con modificadores
"[bright_red]rojo brillante[/bright_red]"
"[dark_green]verde oscuro[/dark_green]"

# Combinación de color y estilo
"[bold cyan]cyan en negritas[/bold cyan]"
"[italic yellow]amarillo en itálicas[/italic yellow]"
```

### Estilos Predefinidos de argparse

Rich-argparse define estilos especiales que puedes usar:

```python
"[argparse.prog]nombre-programa[/argparse.prog]"  # Nombre del programa
"[argparse.args]--opción[/argparse.args]"          # Argumentos
"[argparse.groups]Grupo[/argparse.groups]"         # Nombres de grupos
```

### Backticks para Código

Texto entre backticks se resalta automáticamente con el estilo `argparse.syntax`:

```python
description="Este comando usa `debootstrap` y `schroot`"
# Los backticks se renderizan con estilo bold por defecto
```

## Aplicación Práctica para wine-chroot

### Patrón Recomendado para Descripciones

Para mantener consistencia en todos los comandos:

```python
description="[bold]{command}[/bold] [bold italic]command:[/bold italic] {descripción detallada}"
```

**Ejemplo:**

```python
run_parser = subparsers.add_parser(
    "run",
    help="Run a Windows application",
    description="[bold]run[/bold] [bold italic]command:[/bold italic] Execute a Windows application inside the chroot using Wine",
    formatter_class=RichHelpFormatter,
)
```

### Ejemplos por Tipo de Contenido

#### 1. Comandos y ejecutables

```python
"Execute using [cyan]wine[/cyan] and [cyan]schroot[/cyan]"
"Path to [cyan].exe[/cyan] file"
```

#### 2. Archivos y paths

```python
"Configuration file: [yellow]~/.config/wine-chroot.toml[/yellow]"
"Install to [cyan]/srv/debian-amd64[/cyan]"
```

#### 3. Valores por defecto

```python
"Chroot name (default: [yellow]debian-amd64[/yellow])"
```

#### 4. Advertencias

```python
"[bold red]Warning:[/bold red] This operation requires root access"
"[yellow]Note:[/yellow] This may take several minutes"
```

#### 5. Énfasis en palabras clave

```python
"Show [bold]current[/bold] configuration"
"Extract icon [italic]automatically[/italic]"
"[bold]Required[/bold] system packages"
```

#### 6. Listas multilinea

```python
description=(
    "[bold]config[/bold] [bold italic]command:[/bold italic] "
    "Display current configuration settings.\n\n"
    "Configuration priority:\n"
    "  1. [cyan]--config[/cyan] command line argument\n"
    "  2. [cyan]~/.config/wine-chroot.toml[/cyan]\n"
    "  3. [cyan]/etc/wine-chroot.toml[/cyan]\n"
    "  4. [dim]Built-in defaults[/dim]"
)
```

## Personalización de Estilos Globales

Puedes modificar los estilos por defecto de `RichHelpFormatter`:

```python
from rich_argparse import RichHelpFormatter

# Cambiar estilos globales
RichHelpFormatter.styles["argparse.text"] = "default"  # Descripción normal
RichHelpFormatter.styles["argparse.prog"] = "bold magenta"  # Nombre del programa
RichHelpFormatter.styles["argparse.args"] = "cyan"  # Argumentos como --help
RichHelpFormatter.styles["argparse.groups"] = "yellow"  # Grupos de comandos
RichHelpFormatter.styles["argparse.syntax"] = "bold green"  # Texto en backticks
RichHelpFormatter.styles["argparse.metavar"] = "italic"  # Metavariables
RichHelpFormatter.styles["argparse.default"] = "dim"  # %(default)s
```

### Estilos Disponibles

| Clave | Uso | Default |
|-------|-----|---------|
| `argparse.text` | Descriptions, epilog, --version | `default` |
| `argparse.prog` | Program name | `bold` |
| `argparse.args` | Options like --help | `cyan` |
| `argparse.groups` | Group names (positional arguments, options, commands) | `dark_orange` |
| `argparse.help` | Help text | `default` |
| `argparse.metavar` | Metavariables like PATH, FILE | `bold yellow` |
| `argparse.syntax` | Backtick-quoted text | `bold` |
| `argparse.default` | %(default)s in help | `italic` |

## Casos Especiales

### Deshabilitar Markup

Si necesitas usar corchetes literales `[` `]` en tu texto:

```python
# Opción 1: Escapar con backslashes
"Use [bold]\\[optional\\][/bold] arguments"

# Opción 2: Deshabilitar markup globalmente
RichHelpFormatter.text_markup = False  # Para descriptions/epilog
RichHelpFormatter.help_markup = False  # Para help de argumentos
```

### Renderizables de Rich

Puedes usar cualquier renderable de Rich en descriptions y epilog:

```python
from rich.markdown import Markdown
from rich.table import Table

# Markdown
description = Markdown("""
# Mi Programa

- Feature 1
- Feature 2
""", style="argparse.text")

parser = argparse.ArgumentParser(
    description=description,
    formatter_class=RichHelpFormatter,
)

# Tablas (aunque generalmente no se recomienda para CLI help)
```

## Ejemplo Completo para wine-chroot

```python
from rich_argparse import RichHelpFormatter

# Opcional: personalizar estilos
RichHelpFormatter.styles["argparse.prog"] = "bold magenta"

parser = argparse.ArgumentParser(
    prog="wine-chroot",
    description="Run Windows applications on ARM64 Linux using [bold cyan]Wine[/bold cyan] in a chroot",
    formatter_class=RichHelpFormatter,
)

subparsers = parser.add_subparsers(dest="command")

init_parser = subparsers.add_parser(
    "init",
    help="Initialize a new chroot environment",
    description=(
        "[bold]init[/bold] [bold italic]command:[/bold italic] "
        "Create and configure a new Debian amd64 chroot with Wine installed. "
        "This automates `debootstrap`, `schroot` configuration, and Wine setup."
    ),
    formatter_class=RichHelpFormatter,
)

init_parser.add_argument(
    "-n",
    "--name",
    help="Chroot name (default: [yellow]debian-amd64[/yellow])",
)

init_parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show what would be done [italic]without making changes[/italic]",
)
```

## Testing

Prueba tus cambios con:

```bash
# Ver ayuda principal
uv run wine-chroot --help

# Ver ayuda de un comando específico
uv run wine-chroot init --help
uv run wine-chroot run --help
```

## Referencias

- [Rich-argparse GitHub](https://github.com/hamdanal/rich-argparse)
- [Rich Style Documentation](https://rich.readthedocs.io/en/latest/style.html)
- [Rich Console Markup](https://rich.readthedocs.io/en/latest/markup.html)
