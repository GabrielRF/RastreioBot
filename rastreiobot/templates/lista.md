{% for pacote in pacotes %}
- {{ pacote }}
{% else %}
Nenhum pacote encontrado
{% endfor %}
