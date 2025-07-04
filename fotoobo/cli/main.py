"""
This is the main cli module. If fotoobo is started from the command line the main script starts
app() from within here. Every level of the command line tool is represented by a subdirectory.
If you extend the cli make sure you are in the correct directory or create a new one if there are
more than a few subcommands.

Caution: Use docstrings with care as they are used to print help texts on any command.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from fotoobo import tools
from fotoobo.helpers import cli_path
from fotoobo.helpers.config import config
from fotoobo.helpers.log import Log
from fotoobo.helpers.output import print_logo

from . import convert, get
from .cloud import cloud
from .ems import ems
from .faz import faz
from .fgt import fgt
from .fmg import fmg

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
    rich_markup_mode="rich",
)
log = logging.getLogger("fotoobo")


def version_callback(value: bool) -> None:
    """The version callback"""
    if value:
        if not config.no_logo:
            print_logo()

        get.version(False)
        raise typer.Exit()


@app.callback()
def callback(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    context: typer.Context,
    config_file: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Set the fotoobo configuration file.",
            show_default=False,
            metavar="[file]",
        ),
    ] = None,
    log_level: Annotated[
        Optional[str],
        typer.Option(
            "--loglevel",
            help="Set the log level. Choose from CRITICAL, ERROR, WARNING, INFO, DEBUG.",
            metavar="[level]",
            show_default=False,
        ),
    ] = None,
    nologo: Annotated[
        Optional[bool], typer.Option("--nologo", help="Do not print the beautiful fotoobo logo.")
    ] = None,
    log_quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Disable console logging.", show_default=False)
    ] = False,
    version: Annotated[  # pylint: disable=unused-argument
        Optional[bool],
        typer.Option(
            "--version", "-V", help="Print the fotoobo version.", callback=version_callback
        ),
    ] = None,
) -> None:
    """
    The Fortinet Toolbox (fotoobo) - make IT easy

    ─────────────────────────────────────────────

    This is fotoobo, the mighty [bold]Fo[/bold]rtinet [bold]too[/bold]l[bold]bo[/bold]x for
    managing your Fortinet environment. It is meant to be extendable to your needs.

    For detailed documentation see https://fotoobo.readthedocs.io.
    """
    config.load_configuration(config_file)
    config.no_logo = True if nologo else config.no_logo

    if log_level:
        log_level = log_level.upper()

    Log.configure_logging(log_quiet, log_level)

    if not config.no_logo:
        print_logo()

    log.debug("Let the magic begin")

    # Log all the configuration options
    # If a config option is a data-structure (dict) unpack it and write it line-by-line
    # For security reasons all sensitive values are shortened
    for attr in dir(config):
        if attr.startswith("_") or attr in ["config", "load_configuration"]:
            continue

        if attr in ["audit_logging", "logging", "vault"] and getattr(config, attr):
            for sub_attr, value in getattr(config, attr).items():
                if attr == "vault" and sub_attr in ["role_id", "secret_id"]:
                    value = f"{value[:4]}...{value[-4:]}"

                log.debug("Option '%s.%s' is '%s'", attr, sub_attr, value)

            continue

        log.debug("Option '%s' is '%s'", attr, getattr(config, attr))

    cli_path.append(str(context.invoked_subcommand))
    log.debug("About to execute command: '%s'", context.invoked_subcommand)
    log.audit(f'command="{" ".join(sys.argv)}"')  # type: ignore
    config.cli_info = context.to_info_dict()


@app.command(hidden=True)
def greet(
    name: Annotated[
        Optional[str],
        typer.Argument(
            help="The name of the person to greet.", show_default=False, metavar="[name]"
        ),
    ] = None,
    bye: Annotated[bool, typer.Option("--bye", "-b", help='Also write "bye" at the end.')] = False,
    log_enabled: Annotated[bool, typer.Option("--log", "-l", help="Enable logging.")] = False,
) -> None:
    """
    This is the hidden greeting function.
    It allows you to greet someone with different colors in different languages.
    """
    if not name:
        try:
            name = os.getlogin().capitalize()

        except OSError:  # We need this, will fail on GitHub otherwise...
            name = ""

    tools.greet(str(name), bye, log_enabled)


# fotoobo specific commands
app.add_typer(convert.app, name="convert", help="Convert commands for fotoobo.")
app.add_typer(get.app, name="get", help="Get information about fotoobo or your configuration.")

# commands for the Fortinet products
app.add_typer(ems.app, name="ems", help="Commands for FortiClient EMS.")
app.add_typer(faz.app, name="faz", help="Commands for FortiAnalyzer.")
app.add_typer(cloud.app, name="cloud", help="Commands for FortiCloud applications.")
app.add_typer(fgt.app, name="fgt", help="Commands for FortiGate.")
app.add_typer(fmg.app, name="fmg", help="Commands for FortiManager.")
