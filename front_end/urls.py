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
    path('vendas/', views.Vendas, name='vendas'),
    path('registrar-venda/', views.registrar_venda, name='registrar_venda'),
    path('configuracoes/', views.Configuracoes, name='configuracoes'),
]