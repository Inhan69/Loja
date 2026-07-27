from decimal import Decimal, InvalidOperation
import json

from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProdutoForm, Edit_ProdutoForm, ClientForm, EditClientForm
from .models import Produto, Client, Venda
from django.http import HttpRequest, JsonResponse
from django.db.models import IntegerField, Q
from django.db.models.functions import Cast

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

    produtos = Produto.objects.all()
    if termo_busca:
        produtos = produtos.filter(
            Q(nome__icontains=termo_busca) | Q(codigo__icontains=termo_busca)
        )

    estoque_ordenado = produtos.annotate(
        codigo_int=Cast('codigo', output_field=IntegerField())
    ).order_by('codigo_int')
    
    contexto = {
        "form": ProdutoForm(),
        "formulario": Edit_ProdutoForm(prefix="edit"), 
        "Estoque": estoque_ordenado,
        "busca": termo_busca,
    }
    return render(request, "pag_produtos.html", contexto)

def sugestoes_produto(request: HttpRequest):
    termo_busca = request.GET.get("q", "").strip()
    if not termo_busca:
        return JsonResponse({"results": []})

    produtos = (
        Produto.objects.filter(
            Q(nome__icontains=termo_busca) | Q(codigo__icontains=termo_busca)
        )
        .annotate(codigo_int=Cast("codigo", output_field=IntegerField()))
        .order_by("codigo_int")[:8]
    )

    results = [{"nome": produto.nome, "codigo": produto.codigo} for produto in produtos]
    return JsonResponse({"results": results})

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
    mostrar_form = request.GET.get("view") == "form"
    form = ClientForm()

    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("front_end:clientes")
        mostrar_form = True

    clientes = Client.objects.all().order_by("-dt_criacao")
    if termo_busca:
        filtro = (
            Q(nome__icontains=termo_busca)
            | Q(cpf__icontains=termo_busca)
            | Q(telefone__icontains=termo_busca)
            | Q(rua__icontains=termo_busca)
            | Q(bairro__icontains=termo_busca)
        )
        if termo_busca.isdigit():
            filtro = filtro | Q(numero=int(termo_busca))
        clientes = clientes.filter(filtro)

    contexto = {
        "clientes": clientes,
        "busca": termo_busca,
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
                    "tipo_pagamento": venda.get_tipo_pagamento_display(),
                    "observacao": venda.observacao,
                    "dt_venda": venda.dt_venda.strftime("%d/%m/%Y %H:%M"),
                }
                for venda in vendas
            ],
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

    produtos = Produto.objects.all()
    if termo_busca:
        produtos = produtos.filter(
            Q(nome__icontains=termo_busca) | Q(codigo__icontains=termo_busca)
        )

    produtos = produtos.annotate(
        codigo_int=Cast("codigo", output_field=IntegerField())
    ).order_by("codigo_int")

    clientes = Client.objects.all().order_by("nome")

    contexto = {
        "produtos": produtos,
        "clientes": clientes,
        "busca": termo_busca,
        "pagamentos": Venda.PAGAMENTO_CHOICES,
    }
    return render(request, "pag_vendas.html", contexto)


def _criar_venda(produto, quantidade, desconto, tipo_pagamento, cliente=None, observacao=""):
    preco_com_desconto = produto.preco - (desconto * produto.preco / Decimal("100"))
    total = preco_com_desconto * quantidade
    if total < 0:
        total = Decimal("0")

    produto.quantidade -= quantidade
    produto.save()

    Venda.objects.create(
        produto=produto,
        cliente=cliente,
        observacao=observacao,
        quantidade=quantidade,
        desconto=desconto,
        tipo_pagamento=tipo_pagamento,
        total=total,
    )


def registrar_venda(request: HttpRequest):
    if request.method != "POST":
        return redirect("front_end:vendas")

    tipo_pagamento = request.POST.get("tipo_pagamento", "dinheiro")
    if tipo_pagamento not in dict(Venda.PAGAMENTO_CHOICES):
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
        cliente_id = request.POST.get("cliente_id", "").strip()
        if cliente_id:
            cliente = Client.objects.filter(id=cliente_id).first()

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


