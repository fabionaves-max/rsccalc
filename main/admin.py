from django.contrib import admin
from .models import Servidor, CriterioRequisito, RequerimentoRSC, AtividadeComprovada

@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'matricula_siape', 'cargo')
    search_fields = ('nome', 'matricula_siape')
    list_filter = ('cargo',)

@admin.register(CriterioRequisito)
class CriterioRequisitoAdmin(admin.ModelAdmin):
    # 'get_requisito_display' renderiza o texto legível da tupla (ex: 'Requisito I...')
    list_display = ('get_requisito_display', 'item', 'pontos', 'descricao_curta')
    list_filter = ('requisito',)
    search_fields = ('descricao',)
    ordering = ('requisito', 'item')

    def descricao_curta(self, obj):
        return obj.descricao[:75] + '...' if len(obj.descricao) > 75 else obj.descricao
    descricao_curta.short_description = 'Descrição'

class AtividadeComprovadaInline(admin.TabularInline):
    model = AtividadeComprovada
    extra = 1
    autocomplete_fields = ['criterio']

@admin.register(RequerimentoRSC)
class RequerimentoRSCAdmin(admin.ModelAdmin):
    list_display = ('servidor', 'data_solicitacao', 'pontuacao_total', 'nivel_alcancado', 'deferido')
    list_filter = ('deferido', 'nivel_alcancado', 'data_solicitacao')
    search_fields = ('servidor__nome', 'servidor__matricula_siape')
    inlines = [AtividadeComprovadaInline]
    readonly_fields = ('pontuacao_total', 'nivel_alcancado')