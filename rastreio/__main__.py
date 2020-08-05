import click
from time import sleep

from rastreio import workers


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dry-run", is_flag=True, help="Does not commit any changes on database")
def clean_packages(dry_run):
    """Clean old and duplicated packages"""
    click.secho("Cleaning old and duplicated packages...", fg="green" if dry_run else "red")
    workers.clean_packages.run(dry_run)


if __name__ == "__main__":
    cli(prog_name="rastreio")
