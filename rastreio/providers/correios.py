import asyncio
from datetime import datetime
from datetime import timedelta
from typing import Optional, Union
from utils import status

import aiohttp


def add_emojis(text):
    casos = {
        'Objeto saiu para entrega ao destinatário': '🚚',
        'Objeto entregue ao destinatário': '🎁',
        'Objeto recebido pelos Correios do Brasil': '📥',
        'Objeto aguardando retirada no endereço indicado': '🏢',
        'Objeto encaminhado para fiscalização aduaneira de exportação': '↗️',
        'Objeto postado': '📦',
        'Liberado sem tributação': '🎉',
        'Aguardando pagamento do despacho postal': '🔫',
        'Pagamento confirmado': '💸',
        'Objeto apreendido por órgão de fiscalização': '👮',
        'Objeto dispensado do pagamento de impostos': '🎉',
        'Aguardando pagamento': '💳\n<a href="https://www.correios.com.br">Acesse o site dos Correios para fazer o pagamento</a>',
    }
    if casos.get(text):
        return f'{text} {casos.get(text)}'
    return text


def get_local(unidade):
    nome = unidade.get('nome')
    if nome: return nome.title()

    bairro = unidade['endereco'].get('bairro', '')
    complemento = unidade['endereco'].get('complemento', '')
    logradouro = unidade['endereco'].get('logradouro', '')
    numero = unidade['endereco'].get('numero', '')

    cidade = unidade.get('cidade', '')
    uf = unidade.get('uf', '')

    #local = f'{cidade.title()} {uf.upper()}'
    local = f'{bairro} {complemento} {logradouro} {numero} {cidade.title()} {uf.upper()}'
    return local.strip()


def format_object(data):
    if 'SRO-020' in str(data['objetos'][0]):
        return status.NOT_FOUND
    stats = []
    stats.append(str(u'\U0001F4EE') +
        '<a href="https://t.me/rastreiobot?start=' +
        data['objetos'][0]['codObjeto'] +
        '">' + data['objetos'][0]['codObjeto'] + '</a>')
    start_date = datetime.strptime(
        data['objetos'][0]['eventos'][-1]["dtHrCriado"],
        '%Y-%m-%dT%H:%M:%S'
    )
    for evento in reversed(data['objetos'][0]['eventos']):
        date = datetime.strptime(evento["dtHrCriado"], '%Y-%m-%dT%H:%M:%S')
        date_delta = date - start_date
        date = date.strftime('%d/%m/%Y %H:%M')
        if date_delta.days > 0:
            date = f'{date} ({date_delta.days} dias)'
        local = get_local(evento["unidade"])
        situacao = evento['descricao']
        try:
            observacao = get_local(evento["unidadeDestino"])
        except KeyError:
            observacao = ''
        situacao = add_emojis(situacao)
        message = f'Data: {date}\nLocal: {local}'
        if situacao: message = f'{message}\nSituação: {situacao}'
        if observacao: message = f'{message}\nObservação: {observacao}'
        stats.append(message)
    return stats


class CorreiosException(Exception):
    pass


class Correios:
    def __init__(self, token: str):
        self.token = token
        self.app_token = None
        self.app_token_updated_at = None

    def should_update_app_token(self) -> bool:
        if not self.app_token:
            return True

        now = datetime.now()
        diff = now - self.app_token_updated_at
        if diff > timedelta(hours=12):
            return True

        return False

    async def get_app_token(self, session: aiohttp.ClientSession) -> str:
        if self.should_update_app_token():
            headers = {
                "content-type": "application/json",
                "user-agent": "Dart/2.18 (dart:io)",
            }

            body = {
                "requestToken": self.token
            }

            response = await session.post(
                url="https://proxyapp.correios.com.br/v1/app-validation",
                headers=headers,
                json=body,
            )

            if not response.ok:
                text = await response.text()
                raise CorreiosException(f"Failed to retrieve app_check_token. status={response.status}, text={text}")

            data = await response.json()
            self.app_token = data["token"]
            self.app_token_updated_at = datetime.now()

        return self.app_token

    async def request(self, url: str, session: aiohttp.ClientSession) -> dict:
        app_token = await self.get_app_token(session)
        headers = {
            "content-type": "application/json",
            "user-agent": "Dart/2.18 (dart:io)",
            "app-check-token": app_token,
        }

        response = await session.get(url, headers=headers)
        if not response.ok:
            raise CorreiosException(f"API request failed. status_code={response.status}, url={url}")

        data = await response.json()
        return data

    async def _request_get_code(self, code: str, session: aiohttp.ClientSession) -> dict:
        url = f"https://proxyapp.correios.com.br/v1/sro-rastro/{code}"
        data = await self.request(url, session)
        try:
            return code, format_object(data)
        except:
            from pprint import pprint
            pprint(data)
            pprint(code)
            raise

    async def get(self, code: str) -> dict:
        async with aiohttp.ClientSession() as session:
            code, updates = await self._request_get_code(code, session)
            return {codes: updates}

    async def get_multiple_packages(self, codes):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._request_get_code(code, session)
                for code in codes
            ]
            data = await asyncio.gather(*tasks)

        return {
            code: updates
            for code, updates in data
        }

if __name__ == "__main__":
    import sys
    from pprint import pprint
    correios = Correios("YW5kcm9pZDtici5jb20uY29ycmVpb3MucHJlYXRlbmRpbWVudG87RjMyRTI5OTc2NzA5MzU5ODU5RTBCOTdGNkY4QTQ4M0I5Qjk1MzU3OA")
    data = asyncio.run(correios.get_multiple_codes(sys.argv[1:]))
    pprint(data)
