banned = '\U0000274C Usuário banido'

user = (
    '\U0001F4EE <b>@RastreioBot!</b>\n\n'
    'Por favor, envie um código de objeto.\n\n'
    'Para adicionar uma descrição, envie um código '
    'seguido da descrição.\n\n'
    '<i>PN123456789BR Minha encomenda</i>'
)

group = (
    '\U0001F4EE <b>@RastreioBot!</b>\n\n'
    'Por favor, envie um código de objeto.\n\n'
    'Para adicionar uma descrição, envie um código '
    'seguido da descrição.\n\n'
    '<i>/PN123456789BR Minha encomenda</i>'
)

error_sys = (
    '\n\n'
    '\U000026A0 <b>Atenção</b>\n'
    'Sistema dos Correios indisponível.\n'
    'Os alertas poderão atrasar.'
)

not_found = (
    'Código não foi encontrado no sistema dos Correios.\n'
    'Talvez seja necessário aguardar algumas horas para '
    'que esteja disponível para consultas.'
)

not_found_tm = 'Código não encontrado no sistema.'

typo = (
    'Erro.\n'
    'Verifique se o código foi digitado corretamente.\n'
    'Caso precise de ajuda, clique em /info ou /gif.'
)

howto = (
    '\U0001F4EE <b>@RastreioBot</b>\n\n'
    '\U0001F579 <b>Instruções</b>\n'
    'Envie para o bot o código de rastreio seguido da descrição do pacote.\n'
    '<code>PN123456789BR Minha encomenda</code>\n'
    'Para editar a descrição, repita o procedimento.\n'
    'Utilize <code>/del</code> para remover pacotes.\n\n'
    'Dúvidas? Clique em /gif.\n\n'
    '\U0001F4D6<b>Bot open source:</b>\n'
    'https://github.com/GabrielRF/RastreioBot\n\n'
    '\U0001F680<b>Conheça meus outros projetos:</b>\n'
    'http://grf.xyz/\n\n'
    '\U0001F4B5 <b>Colabore!</b>\n'
    'Clique em /doar, doe usando PIX ou pelo PicPay, usuario GabrielRF.\n'
    'PIX: pix@rastreiobot.xyz\n'
    'PicPay: http://grf.xyz/picpay\n\n'
    '\U0001F4B3 <b>Rastreie pacotes internacionais e ajude o bot!</b>\n'
    'Envie /pagar para pagar pelo Telegram\n'
    'Ou envie /assinei para pagar pelo PicPay \n\n'
)

error_bot = 'Ops!\nHouve um problema com o bot.\nTente novamente mais tarde.'

premium = (
    'O @RastreioBot é grátis e a idéia é que permaneça assim.'
    '\nPorém, para rastrear pacotes internacionais é necessário pagamento.'
    '\n\nOpções de pagamento:'
    '\n\n1: <b>Pague pelo Telegram</b> com o comando /pagar'
    '\n\n2: <a href="https://grf.xyz/assine">Assine pelo PicPay clicando aqui</a>'
    '\nou buscando por <code>@GabRF</code> no PicPay.'
    '\nCaso já tenha assinado, por favor, envie <code>/assinei seu_usuario_picpay</code>'
    '\nExemplo: <code>/assinei GabRF</code>'
)

patreon = (
    '\n'
    '\U0001F4B5 <b>Colabore!</b>\n'
    'http://grf.xyz/paypal'
)

not_found = 'Nenhum pacote encontrado.'

remove = (
    'Envie <code>/del código do pacote</code> para excluir o pacote de sua lista.\n\n'
    '<code>/del PN123456789CD</code>'
)

desc = (
    'Você sabia que é possível descrever um pacote?\n'
    'Clique em /start para ver um exemplo.'
)

invalid = (
    '<b>Conheça a nuvem privada do Telegram!</b>\n\n'
    'O app disponibiliza a aba de "Mensagens salvas" onde tudo pode ser armazenado!\n\n'
    'Desde textos, fotos e gifs até documentos/arquivos (limitados a 2GB cada)!\n'
    'Para acessar esse chat, clique no link abaixo.\n'
    'Esta é a forma mais fácil e segura de armazenar os seus dados.\n\n'
    '<a href="tg://user?id={}">Mensagens Salvas</a>\n\n'
    'Dúvidas? @GabrielRF'
)

conf_ok  = ('Muito obrigado pela assinatura!\nA configuração já está ok.')

signed = ('Configuração concluída.\n\n'
    'Para alterações, dúvidas ou problemas, fale com @GabrielRF'
)

payment = (
    '\U0001F4EE <b>@RastreioBot</b>\n\n'
    '<b>Condições do pagamento</b>'
    '\n- O bot te enviará lembretes restando 15 e 7 dias para o fim do plano, além de uma mensagem no último dia.'
    '\n- Para acrescentar mais dias, basta repetir a compra.'
    '\n\n<b>Atenção</b>'
    '\n- Pagamento não reembolsável'
    '\n- Este método de pagamento substituirá o PicPay! Ou seja, cancele o plano no PicPay após o pagamento usando este método.'
)

donate_warn = '<b>Atenção</b>\n\nA doação não tem efeito para rastrear encomendas internacionais!\n\nPara rastrear pacotes fora dos Correios, envie /pagar ou acesse https://grf.xyz/assine (<code>GabRF</code> no PicPay).'

donate_ok = (
    'Muito obrigado pela colaboração!'
)

donate_error = (
    'Por favor, tente novamente em alguns minutos.\n'
    'Houve algum erro na transação.\n'
    'Não houve cobrança em seu cartão.'
)

days_left_15 = (
    '<b>RastreioBot</b>'
    '\nRestam apenas 15 dias de rastreio de pacotes internacionais.'
    '\nPara renovar, envie /pagar.'
)

days_left_7 = (
    '<b>RastreioBot</b>'
    '\nRestam apenas 7 dias de rastreio de pacotes internacionais.'
    '\nPara renovar, envie /pagar.'
)

days_left_1 = (
    '<b>RastreioBot</b>'
    '\nRestam apenas 1 dia de rastreio de pacotes internacionais.'
    '\nPara renovar, envie /pagar.'
)
