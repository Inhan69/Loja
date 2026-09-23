from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProdutoForm, Edit_ProdutoForm, ClientForm, EditClientForm
from .models import Produto, Client, Venda, PagamentoParcial
from django.http import HttpRequest, JsonResponse
from django.db import transaction
from django.db.models import Count, F, IntegerField, Sum
from django.db.models.functions import Cast, Coalesce, TruncDate
from django.utils import timezone
from .search_filters import CAMPO_PADRAO_CLIENTE, CAMPO_PADRAO_PRODUTO, filtrar_clientes, filtrar_produtos

ZERO = Decimal("0.00")


def _money(valor):
    if valor is None:
        return ZERO
    return Decimal(valor)


def _saldo_venda(venda):
    restante = _money(venda.total) - _money(venda.valor_pago)
    return restante if restante > 0 else ZERO


def _rotulo_status(venda):
    if venda.status == "anotado" and _money(venda.valor_pago) > 0:
        return "Haver"
    return venda.get_status_display()


def _badge_status(venda):
    if venda.status == "anotado" and _money(venda.valor_pago) > 0:
        return "haver"
    return venda.status


def _rotulo_pagamento(tipo, parcelas=1):
    rotulo = dict(Venda.PAGAMENTO_CHOICES).get(tipo, tipo)
    if tipo == "cartao_credito":
        return f"{rotulo} ({max(1, int(parcelas or 1))}x)"
    return rotulo


def _ler_parcelas(dados, tipo_pagamento):
    if tipo_pagamento != "cartao_credito":
        return 1
    try:
        parcelas = int(str(dados.get("parcelas", "1")).strip() or "1")
    except (TypeError, ValueError):
        return None
    if parcelas < 1 or parcelas > 12:
        return None
    return parcelas


def _venda_api(venda):
    ultimo = venda.pagamentos_parciais.order_by("-dt_pagamento").first()
    tipo = venda.tipo_pagamento
    parcelas = venda.parcelas or 1
    if venda.status == "anotado" and ultimo:
        tipo = ultimo.tipo_pagamento
        parcelas = ultimo.parcelas or 1
    return {
        "id": venda.id,
        "produto": venda.produto.nome,
        "codigo": venda.produto.codigo,
        "quantidade": str(venda.quantidade),
        "total": str(venda.total),
        "valor_pago": str(_money(venda.valor_pago)),
        "saldo": str(_saldo_venda(venda)),
        "desconto": str(venda.desconto),
        "tipo_pagamento": venda.tipo_pagamento,
        "parcelas": parcelas,
        "tipo_pagamento_label": _rotulo_pagamento(tipo, parcelas)
        if venda.status != "anotado" or ultimo
        else venda.get_tipo_pagamento_display(),
        "status": venda.status,
        "status_badge": _badge_status(venda),
        "status_label": _rotulo_status(venda),
        "observacao": venda.observacao,
        "dt_venda": venda.dt_venda.strftime("%d/%m/%Y %H:%M"),
    }


def _normalizar_dia(valor):
    if hasattr(valor, "date") and not isinstance(valor, date):
        return valor.date()
    return valor


def _serie_diaria(queryset, inicio, hoje):
    agrupado = {
        _normalizar_dia(item["dia"]): _money(item["total"])
        for item in queryset.annotate(dia=TruncDate("dt_venda"))
        .values("dia")
        .annotate(total=Coalesce(Sum("total"), ZERO))
    }
    serie = []
    dia = inicio
    while dia <= hoje:
        serie.append(float(agrupado.get(dia, ZERO)))
        dia += timedelta(days=1)
    return serie

def Home(request):
    return render(request, "index.html", {"is_shell": True})

def Dashboard(request):
    hoje = timezone.localdate()
    inicio_grafico = hoje - timedelta(days=13)
    inicio_mes = hoje.replace(day=1)

    vendas = Venda.objects.select_related("produto", "cliente")
    vendas_pagas = vendas.filter(status="pago")
    vendas_anotadas = vendas.filter(status="anotado")

    faturamento_hoje = _money(
        vendas_pagas.filter(dt_venda__date=hoje, valor_pago=0).aggregate(total=Sum("total"))["total"]
    ) + _money(
        PagamentoParcial.objects.filter(dt_pagamento__date=hoje).aggregate(total=Sum("valor"))["total"]
    )
    faturamento_mes = _money(
        vendas_pagas.filter(dt_venda__date__gte=inicio_mes, valor_pago=0).aggregate(total=Sum("total"))["total"]
    ) + _money(
        PagamentoParcial.objects.filter(dt_pagamento__date__gte=inicio_mes).aggregate(total=Sum("valor"))["total"]
    )
    total_anotado = _money(
        vendas_anotadas.aggregate(total=Sum(F("total") - F("valor_pago")))["total"]
    )
    ticket_medio = _money(vendas_pagas.aggregate(total=Sum("total"))["total"])
    qtd_pagas = vendas_pagas.count()
    if qtd_pagas:
        ticket_medio = (ticket_medio / qtd_pagas).quantize(Decimal("0.01"))

    labels_dias = []
    dia = inicio_grafico
    while dia <= hoje:
        labels_dias.append(dia.strftime("%d/%m"))
        dia += timedelta(days=1)

    serie_pagas = _serie_diaria(
        vendas_pagas.filter(dt_venda__date__gte=inicio_grafico),
        inicio_grafico,
        hoje,
    )
    serie_anotadas = _serie_diaria(
        vendas_anotadas.filter(dt_venda__date__gte=inicio_grafico),
        inicio_grafico,
        hoje,
    )

    pagamentos_qs = (
        vendas_pagas.values("tipo_pagamento")
        .annotate(total=Coalesce(Sum("total"), ZERO), qtd=Count("id"))
        .order_by("-total")
    )
    rotulos_pagamento = dict(Venda.PAGAMENTO_CHOICES)
    pagamentos = [
        {
            "rotulo": rotulos_pagamento.get(item["tipo_pagamento"], item["tipo_pagamento"]),
            "total": float(_money(item["total"])),
            "qtd": item["qtd"],
        }
        for item in pagamentos_qs
        if item["tipo_pagamento"] != "anotado"
    ]

    top_produtos = list(
        vendas_pagas.values("produto__nome", "produto__codigo")
        .annotate(
            total=Coalesce(Sum("total"), ZERO),
            qtd=Coalesce(Sum("quantidade"), ZERO),
        )
        .order_by("-total")
    )

    anotados = list(vendas_anotadas.order_by("-dt_venda"))
    qtd_havers = vendas_anotadas.filter(valor_pago__gt=0).count()

    estoque_baixo = list(
        Produto.objects.filter(quantidade__lte=5).order_by("quantidade", "nome")
    )

    contexto = {
        "hoje": hoje,
        "faturamento_hoje": faturamento_hoje,
        "faturamento_mes": faturamento_mes,
        "total_anotado": total_anotado,
        "ticket_medio": ticket_medio,
        "qtd_vendas_hoje": vendas.filter(dt_venda__date=hoje).exclude(status="devolvido").count(),
        "qtd_anotadas": vendas_anotadas.count(),
        "total_produtos": Produto.objects.count(),
        "total_clientes": Client.objects.count(),
        "anotados": anotados,
        "qtd_havers": qtd_havers,
        "top_produtos": top_produtos,
        "estoque_baixo": estoque_baixo,
        "grafico_vendas": {
            "labels": labels_dias,
            "pagas": serie_pagas,
            "anotadas": serie_anotadas,
        },
        "grafico_pagamentos": pagamentos,
    }
    return render(request, "pag_main.html", contexto)

def view_produto(request:HttpRequest):
    if request.method == "POST":
        form_add = ProdutoForm(request.POST)
        if form_add.is_valid():
            form_add.save()
            return redirect('front_end:produtos')

    termo_busca = request.GET.get("q", "").strip()
    filtro_campo = request.GET.get("campo", CAMPO_PADRAO_PRODUTO).strip() or CAMPO_PADRAO_PRODUTO

    produtos = Produto.objects.all()
    produtos = filtrar_produtos(produtos, filtro_campo, termo_busca)

    estoque_ordenado = produtos.annotate(
        codigo_int=Cast('codigo', output_field=IntegerField())
    ).order_by('codigo_int')
    
    contexto = {
        "form": ProdutoForm(),
        "formulario": Edit_ProdutoForm(prefix="edit"), 
        "Estoque": estoque_ordenado,
        "busca": termo_busca,
        "filtro_campo": filtro_campo,
        "total_produtos": estoque_ordenado.count(),
    }
    return render(request, "pag_produtos.html", contexto)

def editar_produto(request:HttpRequest, id):
    produto = get_object_or_404(Produto, id=id) 
    
    if request.method == "POST":  
        form = Edit_ProdutoForm(request.POST, instance=produto, prefix="edit")
        if form.is_valid():
            form.save()
        
    return redirect('front_end:produtos')

def remover_produto(request:HttpRequest, id):
    Produto.objects.filter(id=id).delete()

    return  redirect('front_end:produtos')

def Cliente(request):
    termo_busca = request.GET.get("q", "").strip()
    filtro_campo = request.GET.get("campo", CAMPO_PADRAO_CLIENTE).strip() or CAMPO_PADRAO_CLIENTE
    mostrar_form = request.GET.get("view") == "form"
    form = ClientForm()

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("front_end:clientes")
        mostrar_form = True

    clientes = Client.objects.all().order_by("-dt_criacao")
    clientes = filtrar_clientes(clientes, filtro_campo, termo_busca)

    contexto = {
        "clientes": clientes,
        "busca": termo_busca,
        "filtro_campo": filtro_campo,
        "mostrar_form": mostrar_form,
        "form": form,
        "total_clientes": clientes.count(),
    }
    return render(request, "pag_clientes.html", contexto)


def notas_cliente(request: HttpRequest, id: int):
    cliente = get_object_or_404(Client, id=id)
    vendas = (
        Venda.objects.filter(cliente=cliente)
        .select_related("produto")
        .prefetch_related("pagamentos_parciais")
        .order_by("-dt_venda")
    )

    return JsonResponse(
        {
            "cliente": {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf": cliente.cpf,
                "telefone": cliente.telefone,
                "rua": cliente.rua,
                "bairro": cliente.bairro,
                "numero": cliente.numero,
                "dt_nascimento": cliente.dt_nascimento.strftime("%d/%m/%Y")
                if cliente.dt_nascimento
                else "-",
                "dt_nascimento_input": cliente.dt_nascimento.isoformat()
                if cliente.dt_nascimento
                else "",
            },
            "vendas": [_venda_api(venda) for venda in vendas],
            "pagamentos": [
                {"valor": valor, "rotulo": rotulo}
                for valor, rotulo in Venda.PAGAMENTO_CHOICES
                if valor != "anotado"
            ],
        }
    )


def pagar_venda(request: HttpRequest, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    try:
        dados = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Dados inválidos."}, status=400)

    tipo_pagamento = dados.get("tipo_pagamento", "dinheiro")
    if tipo_pagamento not in dict(Venda.PAGAMENTO_CHOICES) or tipo_pagamento == "anotado":
        return JsonResponse(
            {"success": False, "error": "Forma de pagamento inválida."},
            status=400,
        )

    parcelas = _ler_parcelas(dados, tipo_pagamento)
    if parcelas is None:
        return JsonResponse(
            {"success": False, "error": "Informe as parcelas do cartão de crédito (1x a 12x)."},
            status=400,
        )

    with transaction.atomic():
        venda = get_object_or_404(
            Venda.objects.select_for_update().select_related("produto"),
            id=id,
        )

        if venda.status != "anotado":
            return JsonResponse(
                {"success": False, "error": "Somente itens anotados podem ser pagos."},
                status=400,
            )

        saldo = _saldo_venda(venda).quantize(Decimal("0.01"))
        if saldo <= 0:
            return JsonResponse(
                {"success": False, "error": "Este item não possui valor em aberto."},
                status=400,
            )

        bruto = dados.get("valor", None)
        if bruto in (None, ""):
            valor = saldo
        else:
            try:
                valor = Decimal(str(bruto).replace(",", ".").strip())
            except (InvalidOperation, TypeError):
                return JsonResponse(
                    {"success": False, "error": "Informe um valor válido."},
                    status=400,
                )

        valor = valor.quantize(Decimal("0.01"))
        if valor <= 0:
            return JsonResponse(
                {"success": False, "error": "O valor pago deve ser maior que zero."},
                status=400,
            )
        if valor > saldo:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Não é possível pagar além do valor em aberto.",
                    "saldo": str(saldo),
                },
                status=400,
            )

        PagamentoParcial.objects.create(
            venda=venda,
            valor=valor,
            tipo_pagamento=tipo_pagamento,
            parcelas=parcelas,
        )
        venda.valor_pago = _money(venda.valor_pago) + valor
        if venda.valor_pago >= venda.total:
            venda.valor_pago = venda.total
            venda.status = "pago"
            venda.tipo_pagamento = tipo_pagamento
            venda.parcelas = parcelas
        venda.save()

    return JsonResponse(
        {
            "success": True,
            "venda": _venda_api(venda),
        }
    )


def devolver_venda(request: HttpRequest, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    venda = get_object_or_404(Venda.objects.select_related("produto"), id=id)

    if venda.status == "devolvido":
        return JsonResponse(
            {"success": False, "error": "Este item já foi devolvido."},
            status=400,
        )

    produto = venda.produto
    produto.quantidade += venda.quantidade
    produto.save()

    venda.status = "devolvido"
    venda.save()

    return JsonResponse(
        {
            "success": True,
            "venda": {
                "id": venda.id,
                "status": venda.status,
                "status_label": venda.get_status_display(),
            },
        }
    )


def _restaurar_estoque_anotado(venda: Venda):
    if venda.status != "anotado":
        return
    produto = venda.produto
    produto.quantidade += venda.quantidade
    produto.save(update_fields=["quantidade"])


def excluir_venda(request: HttpRequest, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    venda = get_object_or_404(Venda.objects.select_related("produto"), id=id)

    with transaction.atomic():
        _restaurar_estoque_anotado(venda)
        venda_id = venda.id
        venda.delete()

    return JsonResponse({"success": True, "venda_id": venda_id})


def excluir_cliente(request: HttpRequest, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    cliente = get_object_or_404(Client, id=id)
    vendas = Venda.objects.filter(cliente=cliente).select_related("produto")

    with transaction.atomic():
        for venda in vendas:
            _restaurar_estoque_anotado(venda)
            venda.delete()
        cliente.delete()

    return JsonResponse({"success": True, "cliente_id": id})


def editar_cliente(request: HttpRequest, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido."}, status=405)

    cliente = get_object_or_404(Client, id=id)

    try:
        dados = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Dados inválidos."}, status=400)

    if not dados.get("dt_nascimento"):
        dados["dt_nascimento"] = ""
    if dados.get("numero") in ("", None):
        dados["numero"] = None

    form = EditClientForm(dados, instance=cliente)
    if not form.is_valid():
        erros = {campo: lista[0] for campo, lista in form.errors.items()}
        return JsonResponse({"success": False, "errors": erros}, status=400)

    cliente = form.save()

    return JsonResponse(
        {
            "success": True,
            "cliente": {
                "id": cliente.id,
                "nome": cliente.nome,
                "cpf": cliente.cpf,
                "telefone": cliente.telefone,
                "rua": cliente.rua,
                "bairro": cliente.bairro,
                "numero": cliente.numero,
                "dt_nascimento": cliente.dt_nascimento.strftime("%d/%m/%Y")
                if cliente.dt_nascimento
                else "-",
                "dt_nascimento_input": cliente.dt_nascimento.isoformat()
                if cliente.dt_nascimento
                else "",
            },
        }
    )

def Vendas(request):
    termo_busca = request.GET.get("q", "").strip()
    filtro_campo = request.GET.get("campo", CAMPO_PADRAO_PRODUTO).strip() or CAMPO_PADRAO_PRODUTO

    produtos = Produto.objects.all()
    produtos = filtrar_produtos(produtos, filtro_campo, termo_busca)

    produtos = produtos.annotate(
        codigo_int=Cast("codigo", output_field=IntegerField())
    ).order_by("codigo_int")

    clientes = Client.objects.all().order_by("nome")

    contexto = {
        "produtos": produtos,   
        "clientes": clientes,
        "busca": termo_busca,
        "filtro_campo": filtro_campo,
        "pagamentos": [
            (valor, rotulo)
            for valor, rotulo in Venda.PAGAMENTO_CHOICES
            if valor != "anotado"
        ],
    }
    return render(request, "pag_vendas.html", contexto)


def _criar_venda(produto, quantidade, desconto, tipo_pagamento, cliente=None, observacao="", parcelas=1):
    preco_com_desconto = produto.preco - (desconto * produto.preco / Decimal("100"))
    total = preco_com_desconto * quantidade
    if total < 0:
        total = Decimal("0")

    produto.quantidade -= quantidade
    produto.save()

    status = "anotado" if tipo_pagamento == "anotado" else "pago"
    if tipo_pagamento != "cartao_credito":
        parcelas = 1

    Venda.objects.create(
        produto=produto,
        cliente=cliente,
        observacao=observacao,
        quantidade=quantidade,
        desconto=desconto,
        tipo_pagamento=tipo_pagamento,
        status=status,
        total=total,
        parcelas=parcelas,
    )


def registrar_venda(request: HttpRequest):
    if request.method != "POST":
        return redirect("front_end:vendas")

    tipo_pagamento = request.POST.get("tipo_pagamento", "dinheiro")
    cliente_id = request.POST.get("cliente_id", "").strip()

    if cliente_id:
        tipo_pagamento = "anotado"
    elif tipo_pagamento not in dict(Venda.PAGAMENTO_CHOICES) or tipo_pagamento == "anotado":
        tipo_pagamento = "dinheiro"

    items_json = request.POST.get("items")
    if items_json:
        try:
            items = json.loads(items_json)
        except json.JSONDecodeError:
            return redirect("front_end:vendas")

        try:
            desconto_geral = Decimal(request.POST.get("desconto", "0") or "0")
        except InvalidOperation:
            desconto_geral = Decimal("0")

        cliente = None
        if cliente_id:
            cliente = Client.objects.filter(id=cliente_id).first()
            if not cliente:
                return redirect("front_end:vendas")

        observacao = request.POST.get("observacao", "").strip()[:200]
        parcelas = _ler_parcelas(request.POST, tipo_pagamento)
        if parcelas is None:
            return redirect("front_end:vendas")

        for item in items:
            produto = get_object_or_404(Produto, id=item.get("produto_id"))
            try:
                quantidade = Decimal(str(item.get("quantidade", "1")))
            except InvalidOperation:
                continue

            if quantidade <= 0 or quantidade > produto.quantidade:
                continue

            _criar_venda(
                produto,
                quantidade,
                desconto_geral,
                tipo_pagamento,
                cliente=cliente,
                observacao=observacao,
                parcelas=parcelas,
            )

        return redirect("front_end:vendas")

    produto = get_object_or_404(Produto, id=request.POST.get("produto_id"))

    try:
        quantidade = Decimal(request.POST.get("quantidade", "1"))
        desconto = Decimal(request.POST.get("desconto", "0"))
    except InvalidOperation:
        return redirect("front_end:produtos")

    if quantidade <= 0 or quantidade > produto.quantidade:
        return redirect("front_end:produtos")

    _criar_venda(
        produto,
        quantidade,
        desconto,
        tipo_pagamento,
        parcelas=_ler_parcelas(request.POST, tipo_pagamento) or 1,
    )

    return redirect("front_end:vendas")

def Configuracoes(request):
    return render(request, "pag_configuracoes.html")