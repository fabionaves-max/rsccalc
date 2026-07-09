from django.db import models
from django.core.validators import FileExtensionValidator
import os
from django.contrib.auth.models import User


class Servidor(models.Model):
    # Relacionamento 1-para-1 com o sistema de login
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='servidor', null=True, blank=True)

    nome = models.CharField(max_length=255)
    matricula_siape = models.CharField(max_length=15, unique=True)
    cargo = models.CharField(max_length=150)

    membro_comissao = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class CriterioRequisito(models.Model):
    REQUISITO_CHOICES = [
        ('I', 'Requisito I - Grupos de Trabalho e Comissões'),
        ('II', 'Requisito II - Projetos Institucionais e Gestão'),
        ('III', 'Requisito III - Premiação em Eventos Públicos'),
        ('IV', 'Requisito IV - Responsabilidades Técnico-Administrativas'),
        ('V', 'Requisito V - Cargos de Direção ou Assessoramento'),
        ('VI', 'Requisito VI - Conhecimento Científico ou Técnico'),
    ]

    requisito = models.CharField(max_length=3, choices=REQUISITO_CHOICES)
    item = models.PositiveIntegerField()
    descricao = models.TextField()
    unidade_medida = models.CharField(max_length=100)
    pontos = models.DecimalField(max_digits=4, decimal_places=1)

    def __str__(self):
        return f"{self.get_requisito_display()} - Item {self.item}"


class RequerimentoRSC(models.Model):
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='requerimentos')
    data_solicitacao = models.DateField(auto_now_add=True)
    deferido = models.BooleanField(null=True, blank=True)
    pontuacao_total = models.DecimalField(max_digits=6, decimal_places=1, default=0.0)
    nivel_alcancado = models.CharField(max_length=20, blank=True)

    submetido = models.BooleanField(default=False)
    data_submissao = models.DateTimeField(null=True, blank=True)

    parecer_comissao = models.TextField(
        blank=True,
        help_text="Justificativa fundamentada da decisão, conforme Art. 15."
    )
    data_avaliacao = models.DateTimeField(null=True, blank=True)
    avaliador = models.ForeignKey(
        Servidor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avaliacoes_realizadas'
    )

    def __str__(self):
        return f"Requerimento {self.id} - {self.servidor.nome}"


    def atualizar_pontuacao_e_nivel(self):
        """
        Calcula a pontuação e define o nível do RSC.
        AGORA IGNORA AS ATIVIDADES RECUSADAS PELA COMISSÃO!
        """
        # Filtra as atividades: pega todas, exceto as que foram explicitamente recusadas (aceita_comissao=False)
        atividades_validas = self.atividades.exclude(aceita_comissao=False)

        # 1. Soma total de pontos (usando apenas as válidas)
        total_pontos = sum(att.criterio.pontos * att.quantidade for att in atividades_validas)
        self.pontuacao_total = total_pontos

        # 2. Conta a quantidade de critérios distintos
        criterios_distintos = atividades_validas.values_list('criterio', flat=True).distinct().count()

        # 3. Lista de requisitos (Anexos I a VI) presentes
        requisitos_presentes = set(atividades_validas.values_list('criterio__requisito', flat=True))

        nivel = ''

        # 4. Avaliação das regras (do Nível VI ao Nível I)
        if total_pontos >= 75 and criterios_distintos >= 7 and 'VI' in requisitos_presentes:
            nivel = 'RSC-PCCTAE VI'
        elif total_pontos >= 52 and criterios_distintos >= 5 and any(r in requisitos_presentes for r in ['IV', 'V', 'VI']):
            nivel = 'RSC-PCCTAE V'
        elif total_pontos >= 30 and criterios_distintos >= 3 and any(
                r in requisitos_presentes for r in ['II', 'IV', 'V', 'VI']):
            nivel = 'RSC-PCCTAE IV'
        elif total_pontos >= 25 and criterios_distintos >= 2:
            nivel = 'RSC-PCCTAE III'
        elif total_pontos >= 15 and criterios_distintos >= 2:
            nivel = 'RSC-PCCTAE II'
        elif total_pontos >= 10:
            nivel = 'RSC-PCCTAE I'

        self.nivel_alcancado = nivel
        self.save(update_fields=['pontuacao_total', 'nivel_alcancado'])


def diretorio_comprovante_siape(instance, filename):
    """
    Gera o caminho de upload dinâmico baseado no SIAPE do servidor,
    organizado por Requisito e Item do decreto.
    Caminho final: comprovantes_rsc/<siape>/requisito_<requisito>/item_<item>/<nome_do_arquivo>
    """
    # 1. Busca o SIAPE navegando até o Servidor
    siape = instance.requerimento.servidor.matricula_siape

    # 2. Busca o Requisito (I, II, III...) e o Item (1, 2, 3...) navegando até o Critério
    requisito = instance.criterio.requisito
    item = instance.criterio.item

    # 3. Limpa o nome do arquivo original (opcional, mas recomendado para evitar espaços e acentos)
    # Aqui vamos usar o nome original, mas você pode usar o módulo 'uuid' se quiser nomes únicos
    nome_arquivo = filename

    # 4. Retorna o caminho formatado
    return f'comprovantes_rsc/{siape}/requisito_{requisito}/item_{item}/{nome_arquivo}'


class AtividadeComprovada(models.Model):
    requerimento = models.ForeignKey(
        RequerimentoRSC,
        on_delete=models.CASCADE,
        related_name='atividades'
    )
    # Atualizado para referenciar o novo nome do modelo
    criterio = models.ForeignKey(
        CriterioRequisito,
        on_delete=models.PROTECT
    )
    quantidade = models.PositiveIntegerField(default=1)

    descricao_atividade = models.TextField(
        blank=True,
        help_text="Descreva brevemente a atividade e como ela contribuiu para a instituição. Este texto ajudará a compor seu Memorial."
    )

    arquivo_comprovante = models.FileField(
        upload_to=diretorio_comprovante_siape,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Anexe o documento comprobatório em formato PDF, conforme Art. 4º."
    )

    aceita_comissao = models.BooleanField(null=True, blank=True)
    justificativa_comissao = models.TextField(blank=True, help_text="Obrigatório caso a atividade seja recusada.")

    def __str__(self):
        return f"{self.criterio} ({self.quantidade}x)"


from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Escuta quando uma AtividadeComprovada for SALVA (criada ou editada)
@receiver(post_save, sender=AtividadeComprovada)
def atividade_salva(sender, instance, **kwargs):
    # Chama o recálculo no requerimento atrelado à atividade
    instance.requerimento.atualizar_pontuacao_e_nivel()

# Escuta quando uma AtividadeComprovada for EXCLUÍDA
@receiver(post_delete, sender=AtividadeComprovada)
def atividade_excluida(sender, instance, **kwargs):
    # Recalcula caso o servidor remova um arquivo/atividade
    instance.requerimento.atualizar_pontuacao_e_nivel()