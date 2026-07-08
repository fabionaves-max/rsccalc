from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),

    # Rota principal do servidor logado
    path('painel/', views.painel_servidor, name='painel_servidor'),

    # Rota de ação (cria o requerimento e redireciona)
    path('requerimento/novo/', views.novo_requerimento, name='novo_requerimento'),

    # Rota com parâmetro (o ID do requerimento) para adicionar anexos
    path('requerimento/<int:requerimento_id>/', views.detalhe_requerimento, name='detalhe_requerimento'),

    path('requerimento/<int:requerimento_id>/finalizar/', views.finalizar_requerimento, name='finalizar_requerimento'),

    path('requerimento/<int:requerimento_id>/pdf/', views.baixar_pdf_memorial, name='baixar_pdf_memorial'),

    path('atividade/<int:atividade_id>/excluir/', views.excluir_atividade, name='excluir_atividade'),

    path('comissao/painel/', views.painel_comissao, name='painel_comissao'),

    path('comissao/avaliar/<int:requerimento_id>/', views.avaliar_requerimento, name='avaliar_requerimento'),

    path('comissao/avaliar-atividade/<int:atividade_id>/', views.avaliar_atividade_individual, name='avaliar_atividade_individual'),

]