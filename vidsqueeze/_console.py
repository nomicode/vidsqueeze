import sys

import click


def _print_error(message):
    click.echo(click.style(f"Error: {message}", fg="red"), err=True)


def _print_status(msg, details=""):
    out = click.style("==>", fg="blue") + " "
    if details:
        msg = f"{msg}:"
    out += click.style(msg, bold=True)
    if details:
        out += f" {details}"
    click.echo(out)
