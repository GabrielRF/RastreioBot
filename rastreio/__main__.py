from time import sleep

import click


@click.group()
def cli():
    pass


@cli.command(name="packages:clean")
@click.option("--dry-run", is_flag=True, help="Does not commit any changes on database")
def clean_packages(dry_run):
    """Clean old and duplicated packages"""
    click.secho("Cleaning old and duplicated packages...", fg="green" if dry_run else "red")

    from rastreio.workers import clean_packages
    clean_packages.run(dry_run)


@cli.command(name="packages:update")
def update_packages():
    """Update active packages"""
    click.secho("Updating packages...", fg="red")

    from rastreio.workers import update_packages
    update_packages.run()


@cli.command(name="packages:delete")
@click.option("--code", help="Package code to be deleted")
def delete_package(code):
    """Delete a package"""
    click.secho("Deleting active package with code {}...".format(code), fg="red")

    from rastreio import db
    db.delete_package(code)


if __name__ == "__main__":
    cli(prog_name="rastreio")
