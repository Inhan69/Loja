from decimal import Decimal, InvalidOperation
import json

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProdutoForm, Edit_ProdutoForm, ClientForm, EditClientForm
from .models import Produto, Client, Venda
from django.http import HttpRequest, JsonResponse
from django.db.models import IntegerField, Q
from django.db.models.functions import Cast
from .search_filters import CAMPO_PADRAO_CLIENTE, CAMPO_PADRAO_PRODUTO, filtrar_clientes, filtrar_produtos

def Home(request):
    return render(request, 'index.html')

def Dashboard(request):
    return render(request, 'pag_main.html')

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
            "vendas": [
                {
                    "id": venda.id,
                    "produto": venda.produto.nome,
                    "codigo": venda.produto.codigo,
                    "quantidade": str(venda.quantidade),
                    "total": str(venda.total),
                    "desconto": str(venda.desconto),
                    "tipo_pagamento": venda.tipo_pagamento,
                    "tipo_pagamento_label": venda.get_tipo_pagamento_display(),
                    "status": venda.status,
                    "status_label": venda.get_status_display(),
                    "observacao": venda.observacao,
                    "dt_venda": venda.dt_venda.strftime("%d/%m/%Y %H:%M"),
                }
                for venda in vendas
            ],
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

    venda = get_object_or_404(Venda, id=id)

    if venda.status != "anotado":
        return JsonResponse(
            {"success": False, "error": "Somente itens anotados podem ser pagos."},
            status=400,
        )

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

    venda.tipo_pagamento = tipo_pagamento
    venda.status = "pago"
    venda.save()

    return JsonResponse(
        {
            "success": True,
            "venda": {
                "id": venda.id,
                "tipo_pagamento": venda.tipo_pagamento,
                "tipo_pagamento_label": venda.get_tipo_pagamento_display(),
                "status": venda.status,
                "status_label": venda.get_status_display(),
            },
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


def _criar_venda(produto, quantidade, desconto, tipo_pagamento, cliente=None, observacao=""):
    preco_com_desconto = produto.preco - (desconto * produto.preco / Decimal("100"))
    total = preco_com_desconto * quantidade
    if total < 0:
        total = Decimal("0")

    produto.quantidade -= quantidade
    produto.save()

    status = "anotado" if tipo_pagamento == "anotado" else "pago"

    Venda.objects.create(
        produto=produto,
        cliente=cliente,
        observacao=observacao,
        quantidade=quantidade,
        desconto=desconto,
        tipo_pagamento=tipo_pagamento,
        status=status,
        total=total,
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

    _criar_venda(produto, quantidade, desconto, tipo_pagamento)

    return redirect("front_end:vendas")

def Configuracoes(request):
    return render(request, "pag_configuracoes.html")