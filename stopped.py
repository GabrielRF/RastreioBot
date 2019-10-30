import configparser

import telebot

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.forward_message('9083329', message.from_user.id, message.message_id)
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.reply_to(message, "O bot está passando por uma rápida manutenção. Em breve tudo estará no ar novamente.")
    except:
        pass

bot.polling()
