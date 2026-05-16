from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProdutoForm, Edit_ProdutoForm, ClientForm
from .models import Produto, Client
from django.http import HttpRequest, JsonResponse
from django.db.models import IntegerField
from django.db.models import Q
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

def Vendas(request):
    return render(request, "pag_vendas.html")

def Configuracoes(request):
    return render(request, "pag_configuracoes.html")


