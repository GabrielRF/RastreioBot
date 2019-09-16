banned = (str(u'\U0000274C') + 'Usuário banido')

user = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
    'Por favor, envie um código de objeto.\n\n' +
    'Para adicionar uma descrição, envie um código ' +
    'seguido da descrição.\n\n' +
    '<i>PN123456789BR Minha encomenda</i>')

group = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
    'Por favor, envie um código de objeto.\n\n' +
    'Para adicionar uma descrição, envie um código ' +
    'seguido da descrição.\n\n' +
    '<i>/PN123456789BR Minha encomenda</i>')

error_sys = ('\n\n' + str(u'\U000026A0') + ' <b>Atenção</b>\n' +
    'Sistema dos Correios indisponível.\n'+
    'Os alertas poderão atrasar.')

not_found = ('Código não foi encontrado no sistema dos Correios.\n'
    + 'Talvez seja necessário aguardar algumas horas para'
    + ' que esteja disponível para consultas.')

not_found_tm = ('Código não encontrado no sistema.')

typo = ('Erro.\nVerifique se o código foi digitado corretamente.\nCaso precise de ajuda, clique em /info ou /gif.')

howto = (str(u'\U0001F4EE') + '<b>@RastreioBot</b>\n\n'
    + str(u'\U0001F579') + '<b>Instruções</b>'
    + '\nEnvie para o bot o código de rastreio seguido da descrição do pacote.'
    + '\n<code>PN123456789BR Minha encomenda</code>'
    + '\nPara editar a descrição, repita o procedimento.'
    + '\nUtilize <code>/del</code> para remover pacotes.'
    + '\n\nDúvidas? Clique em /gif.'
    #+ '\n\n' + str(u'\U00002B50') + '<b>Avalie o bot:</b>'
    #+ '\nhttps://telegram.me/storebot?start=rastreiobot\n\n'
    + '\n\n' + str(u'\U0001F4D6') + '<b>Bot open source:</b>\nhttps://github.com/GabrielRF/RastreioBot'
    + '\n\n' + str(u'\U0001F680') + '<b>Conheça meus outros projetos:</b>'
    + '\nhttp://grf.xyz/telegrambr\n\n'
    + str(u'\U0001F4B5') + '<b>Colabore!</b>'
    + '\nPicPay: http://grf.xyz/picpay\n\n'
    #+ '\nPayPal: http://grf.xyz/paypal'
    #+ '\nPatreon: http://grf.xyz/patreon\n\n'
    + str(u'\U0001F4B3') + '<b>Envie R$ 1 por mês e ajude o bot!</b>'
    + '\nhttp://grf.xyz/assine'
    + '\n\n' + str(u'\U0001F517'))

error_bot = ('Ops!\nHouve um problema com o bot.\nTente novamente mais tarde.')

premium = (
    'Usuãrio não autorizado a rastrear pacotes com este formato.'
    + '\nPara ter acesso a esta funcionalidade é necessário assinar o bot.'
    + '\n<a href="https://grf.xyz/assine">Clique aqui para assinar</a>.'
    + '\n\nCaso já tenha assinado, por favor, fale com @GabrielRF'
    )

patreon = (
    '\n'
    + str(u'\U0001F4B5') + '<b>Colabore!</b>'
    + '\nhttp://grf.xyz/paypal'
    )

not_found = ('Nenhum pacote encontrado.')

remove = ('Envie <code>/del código do pacote</code> para excluir o pacote de sua lista.'
    '\n\n<code>/del PN123456789CD</code>')

desc = ('Você sabia que é possível descrever um pacote?'
    + '\nClique em /start para ver um exemplo.')

invalid = ('<b>Use a nuvem privada do Telegram!</b>\n\nO app disponibiliza a aba de "Mensagens salvas" onde tudo pode ser armazenado!\n\nDesde textos, fotos e gifs até documentos/arquivos (limitados a 1,5GB cada)!\nPara acessar esse chat, clique no link abaixo.\nEsta é a forma mais fácil e segura de armazenar os seus dados.\n\n<a href="tg://user?id={}">Mensagens Salvas</a>\n\nDúvidas? @GabrielRF')
