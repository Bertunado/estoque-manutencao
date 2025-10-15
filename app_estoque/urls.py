from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Dê um nome para o conjunto de URLs da sua aplicação
app_name = 'estoque'

urlpatterns = [
    path('', views.estoque_view, name='estoque_lista'), 
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('retirada/', views.retirada_itens, name='retirada'),
    
    # NOVA URL: Endpoint para adicionar um item ao carrinho
    path('carrinho/adicionar/<int:item_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
    path('estoque/', views.estoque_view, name='estoque_lista'),
    path('estoque/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('retirada/confirmar/', views.confirmar_retirada, name='confirmar_retirada'),
    path('historico/', views.historico_view, name='historico'),
    path('estoque/editar/<int:item_id>/', views.editar_item, name='editar_item'),
    path('historico/aprovar/<int:retirada_id>/', views.aprovar_retirada, name='aprovar_retirada'),
    path('historico/recusar/<int:retirada_id>/', views.recusar_retirada, name='recusar_retirada'),
    path('notificacoes/marcar-como-lido/', views.marcar_notificacoes_como_lidas, name='marcar_como_lido'),
    path('carrinho/atualizar/', views.atualizar_quantidade_carrinho, name='atualizar_quantidade'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('carrinho/limpar/', views.limpar_carrinho, name='limpar_carrinho'),
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('historico/verificar-novas/', views.verificar_novas_retiradas, name='verificar_novas'),
]