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
@click.argument("code", type=str, required=True)
def delete_package(code):
    """Delete a package"""
    click.secho("Deleting active package with code {}...".format(code), fg="red")

    from rastreio import db
    db.delete_package(code)


@cli.command(name="bot:run")
@click.option("--maintenance", is_flag=True, help="Sets bot to maintenance mode")
def run_bot(maintenance):
    if not maintenance:
        return

    import configparser
    config = configparser.ConfigParser()
    config.read('bot.conf')
    TOKEN = config['RASTREIOBOT']['TOKEN']
    admin_id = config['RASTREIOBOT']['admin_id']

    import telebot
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(func=lambda m: True)
    def echo_all(message):
        bot.forward_message(admin_id, message.from_user.id, message.message_id)
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            bot.reply_to(message, "O bot está passando por uma rápida manutenção. Em breve tudo estará no ar novamente.")
        except:
            pass

    bot.polling()

if __name__ == "__main__":
    cli(prog_name="rastreio")
