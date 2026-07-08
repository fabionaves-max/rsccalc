from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import RequerimentoRSC, AtividadeComprovada, CriterioRequisito
from .forms import AtividadeComprovadaForm


@login_required
def painel_servidor(request):
    """ Exibe a lista de requerimentos apenas do servidor logado """
    # Verifica se o usuário logado tem um perfil de servidor associado
    if hasattr(request.user, 'servidor'):
        servidor = request.user.servidor
        # Traz os requerimentos filtrando apenas pelos deste servidor
        requerimentos = RequerimentoRSC.objects.filter(servidor=servidor).order_by('-data_solicitacao')
        return render(request, 'painel_servidor.html', {'requerimentos': requerimentos, 'servidor': servidor})
    else:
        return render(request, 'erro.html',
                      {'mensagem': 'Seu usuário não está vinculado a um cadastro de Servidor (SIAPE).'})


@login_required
def novo_requerimento(request):
    """ Cria um requerimento em branco automaticamente e redireciona para a tela de anexos """
    if hasattr(request.user, 'servidor'):
        # Cria o requerimento no banco de dados
        requerimento = RequerimentoRSC.objects.create(servidor=request.user.servidor)
        # Redireciona para a página onde ele vai inserir as atividades desse requerimento específico
        return redirect('detalhe_requerimento', requerimento_id=requerimento.id)
    return redirect('painel_servidor')


# Importe o timezone e as messages no topo do arquivo
from django.utils import timezone
from django.contrib import messages


@login_required
def detalhe_requerimento(request, requerimento_id):
    servidor = request.user.servidor
    requerimento = get_object_or_404(RequerimentoRSC, id=requerimento_id, servidor=servidor)

    # Processamento do formulário Modal
    if request.method == 'POST' and not requerimento.submetido:
        form = AtividadeComprovadaForm(request.POST, request.FILES)
        if form.is_valid():
            nova_atividade = form.save(commit=False)
            nova_atividade.requerimento = requerimento
            nova_atividade.save()
            messages.success(request, 'Comprovante anexado com sucesso!')
            return redirect('detalhe_requerimento', requerimento_id=requerimento.id)
    else:
        form = AtividadeComprovadaForm()

    # Buscamos todos os critérios ordenados pelo ID (garante a ordem exata da lei)
    todos_criterios = CriterioRequisito.objects.all().order_by('id')
    atividades_salvas = requerimento.atividades.all()

    # Estruturamos os dados agrupando por Requisito (I, II, III...)
    estrutura = {}
    for crit in todos_criterios:
        req_key = crit.requisito
        if req_key not in estrutura:
            estrutura[req_key] = {
                'display': crit.get_requisito_display(),
                'itens': []
            }

        # Filtramos as atividades do servidor que pertencem a este critério específico
        acts = [a for a in atividades_salvas if a.criterio_id == crit.id]

        estrutura[req_key]['itens'].append({
            'criterio': crit,
            'atividades': acts
        })

    contexto = {
        'requerimento': requerimento,
        'form': form,
        'estrutura_requisitos': estrutura.values(),  # Mandamos a lista agrupada para o HTML
    }
    return render(request, 'detalhe_requerimento.html', contexto)

# Nova view para o botão de Finalizar
@login_required
def finalizar_requerimento(request, requerimento_id):
    servidor = request.user.servidor
    requerimento = get_object_or_404(RequerimentoRSC, id=requerimento_id, servidor=servidor)

    if not requerimento.submetido:
        if requerimento.atividades.exists():
            requerimento.submetido = True
            requerimento.data_submissao = timezone.now()
            requerimento.save()
            messages.success(request, 'Requerimento enviado com sucesso para a Comissão Avaliadora!')
        else:
            messages.error(request, 'Você precisa anexar pelo menos um comprovante antes de enviar.')

    return redirect('detalhe_requerimento', requerimento_id=requerimento.id)


@login_required
def excluir_atividade(request, atividade_id):
    """ Exclui uma atividade anexada, desde que o requerimento não tenha sido enviado """
    servidor = request.user.servidor

    # Busca a atividade, garantindo que o requerimento atrelado a ela pertence a este servidor
    atividade = get_object_or_404(AtividadeComprovada, id=atividade_id, requerimento__servidor=servidor)
    requerimento = atividade.requerimento

    # Trava de segurança: só exclui se não estiver submetido
    if not requerimento.submetido:
        # A exclusão vai acionar aquele Signal (post_delete) que criamos para recalcular os pontos
        atividade.delete()
        messages.success(request, 'Atividade removida com sucesso. A pontuação foi recalculada.')
    else:
        messages.error(request, 'Não é possível excluir atividades de um requerimento já enviado para a comissão.')

    return redirect('detalhe_requerimento', requerimento_id=requerimento.id)


from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa  # Importação da biblioteca geradora de PDF
import io
from itertools import groupby  # Importação para agrupar as atividades
from django.http import HttpResponse
from django.template.loader import render_to_string  # Usaremos render_to_string
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader

def pagina_inicial(request):
    """ Exibe a página inicial do sistema com os links de acesso """
    return render(request, 'index.html')

def converter_html_para_pdf(html_content, pdf_writer):
    """ Função auxiliar para renderizar um pedaço de HTML e adicionar ao arquivo final """
    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_content, dest=buffer)

    if not pisa_status.err:
        buffer.seek(0)
        reader = PdfReader(buffer)
        for page in reader.pages:
            pdf_writer.add_page(page)


@login_required
def baixar_pdf_memorial(request, requerimento_id):
    """ Gera o PDF do memorial intercalando texto descritivo e anexos por item """
    servidor = request.user.servidor
    if request.user.servidor.membro_comissao:
        requerimento = get_object_or_404(RequerimentoRSC, id=requerimento_id)
    else:
        requerimento = get_object_or_404(RequerimentoRSC, id=requerimento_id, servidor=servidor)

    # Buscamos as atividades ordenadas
    atividades_salvas = requerimento.atividades.select_related('criterio').order_by('criterio__requisito',
                                                                                    'criterio__item')

    pdf_writer = PdfWriter()

    # 1. Gerar e adicionar a CAPA do Memorial
    capa_html = render_to_string('memorial_capa.html', {
        'requerimento': requerimento,
        'servidor': servidor
    })
    converter_html_para_pdf(capa_html, pdf_writer)

    # 2. Agrupar as atividades por critério e intercalar os PDFs
    # O groupby agrupa itens sequenciais que possuem a mesma chave (o mesmo criterio)
    for criterio, grupo_atividades in groupby(atividades_salvas, key=lambda x: x.criterio):
        lista_atividades = list(grupo_atividades)

        # A. Gerar a página de TEXTO deste Grupo/Item
        item_html = render_to_string('memorial_item.html', {
            'criterio': criterio,
            'atividades': lista_atividades
        })
        converter_html_para_pdf(item_html, pdf_writer)

        # B. Adicionar os ANEXOS reais logo na sequência das páginas de texto
        for atividade in lista_atividades:
            if atividade.arquivo_comprovante and hasattr(atividade.arquivo_comprovante, 'path'):
                try:
                    anexo_reader = PdfReader(atividade.arquivo_comprovante.path)
                    for page in anexo_reader.pages:
                        pdf_writer.add_page(page)
                except Exception as e:
                    print(f"Erro ao mesclar anexo da atividade {atividade.id}: {e}")

    # 3. Preparar o arquivo final para download
    response_buffer = io.BytesIO()
    pdf_writer.write(response_buffer)
    response_buffer.seek(0)

    response = HttpResponse(response_buffer, content_type='application/pdf')
    nome_arquivo = f'Memorial_Intercalado_RSC_{servidor.matricula_siape}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    return response


from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone


# Função que verifica se o usuário tem permissão de comissão
def is_membro_comissao(user):
    return hasattr(user, 'servidor') and user.servidor.membro_comissao


@login_required
@user_passes_test(is_membro_comissao, login_url='painel_servidor')
def painel_comissao(request):
    """ Lista todos os requerimentos submetidos aguardando análise ou já avaliados """
    # Filtra apenas os que já foram enviados pelo servidor
    requerimentos = RequerimentoRSC.objects.filter(submetido=True).order_by('-data_submissao')

    # Separando para facilitar a visualização no template
    pendentes = requerimentos.filter(deferido__isnull=True)
    avaliados = requerimentos.filter(deferido__isnull=False)

    contexto = {
        'pendentes': pendentes,
        'avaliados': avaliados,
    }
    return render(request, 'painel_comissao.html', contexto)


@login_required
@user_passes_test(is_membro_comissao, login_url='painel_servidor')
def avaliar_requerimento(request, requerimento_id):
    """ Tela onde a comissão lê o memorial e emite o parecer """
    requerimento = get_object_or_404(RequerimentoRSC, id=requerimento_id, submetido=True)

    if request.method == 'POST':
        # Pega a decisão do formulário (vem como string 'True' ou 'False')
        decisao = request.POST.get('decisao')
        parecer = request.POST.get('parecer_comissao')

        if decisao in ['True', 'False'] and parecer.strip():
            requerimento.deferido = (decisao == 'True')
            requerimento.parecer_comissao = parecer
            requerimento.data_avaliacao = timezone.now()
            requerimento.avaliador = request.user.servidor
            requerimento.save()

            messages.success(request, 'Avaliação registrada com sucesso!')
            return redirect('painel_comissao')
        else:
            messages.error(request, 'Você deve selecionar Deferido/Indeferido e preencher a justificativa.')

    atividades = requerimento.atividades.select_related('criterio').order_by('criterio__requisito', 'criterio__item')

    contexto = {
        'requerimento': requerimento,
        'atividades': atividades,
    }
    return render(request, 'avaliar_requerimento.html', contexto)


@login_required
@user_passes_test(is_membro_comissao, login_url='painel_servidor')
def avaliar_atividade_individual(request, atividade_id):
    """ Registra se a comissão aceitou ou recusou um comprovante específico """
    atividade = get_object_or_404(AtividadeComprovada, id=atividade_id, requerimento__submetido=True)

    if request.method == 'POST':
        decisao = request.POST.get('decisao')
        justificativa = request.POST.get('justificativa_comissao', '')

        if decisao == 'False' and not justificativa.strip():
            messages.error(request, 'Para recusar uma atividade, é obrigatório preencher a justificativa.')
        elif decisao in ['True', 'False']:
            atividade.aceita_comissao = (decisao == 'True')
            atividade.justificativa_comissao = justificativa
            atividade.save()  # Isso engatilha o recálculo automático!
            messages.success(request, 'Avaliação do item registrada com sucesso.')

    return redirect('avaliar_requerimento', requerimento_id=atividade.requerimento.id)