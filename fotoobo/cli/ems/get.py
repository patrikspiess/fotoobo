"""
The FortiClient EMS get commands
"""

import logging

import typer
from typing_extensions import Annotated

from fotoobo.helpers import cli_path
from fotoobo.tools import ems

app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")
log = logging.getLogger("fotoobo")


@app.callback()
def callback(context: typer.Context) -> None:
    """
    The ems get subcommand callback

    Args:
        context: The context object of the typer app
    """
    cli_path.append(str(context.invoked_subcommand))
    log.debug("About to execute command: '%s'", context.invoked_subcommand)


@app.command()
def version(
    host: Annotated[
        str,
        typer.Argument(
            help="The FortiClientEMS hostname to access (must be defined in the inventory).",
            metavar="[host]",
        ),
    ] = "ems",
) -> None:
    """
    Get the FortiClient EMS version.
    """
    result = ems.get.version(host)
    result.print_result_as_table(
        title="FortiClient EMS Version",
        headers=["FortiClient EMS", "Version"],
    )


@app.command()
def workgroups(
    host: Annotated[
        str,
        typer.Argument(
            help="The FortiClientEMS hostname to access (must be defined in the inventory).",
            metavar="[host]",
        ),
    ] = "ems",
    custom: Annotated[bool, typer.Option("--custom", "-c", help="Only show custom groups")] = False,
) -> None:
    """
    Get the FortiClient EMS workgroups.
    """
    result = ems.get.workgroups(host, custom)
    result.print_result_as_table(
        title="FortiClient EMS Workgroups", headers=["Group", "ID", "Count"]
    )
