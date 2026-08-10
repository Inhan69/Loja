from django.urls import path
from . import views

app_name = 'front_end'

urlpatterns = [
    path('', views.Home),
    path('dashboard/', views.Dashboard, name='dashboard'),
    path('produtos/', views.view_produto, name='produtos'),
    path('produtos/sugestoes/', views.sugestoes_produto, name='sugestoes_produto'),
    path('editar/<int:id>/', views.editar_produto, name='editar'),
    path('remover/<int:id>/', views.remover_produto, name='remover'),
    path('clientes/', views.Cliente, name='clientes'),
    path('clientes/<int:id>/notas/', views.notas_cliente, name='notas_cliente'),
    path('clientes/<int:id>/editar/', views.editar_cliente, name='editar_cliente'),
    path('vendas/<int:id>/pagar/', views.pagar_venda, name='pagar_venda'),
    path('vendas/<int:id>/devolver/', views.devolver_venda, name='devolver_venda'),
    path('vendas/', views.Vendas, name='vendas'),
    path('registrar-venda/', views.registrar_venda, name='registrar_venda'),
    path('configuracoes/', views.Configuracoes, name='configuracoes'),
]