 Sistema RSC-TAE 🎓

[cite_start]Plataforma institucional desenvolvida em **Django** para automatizar, gerenciar e auditar a concessão do Reconhecimento de Saberes e Competências aos servidores ocupantes dos cargos do Plano de Carreira dos Cargos Técnico-Administrativos em Educação (RSC-PCCTAE)[cite: 11, 15].

[cite_start]O sistema foi arquitetado em estrita observância às regras, pontuações e limites estabelecidos pelo **Decreto Nº 13.048, de 3 de julho de 2026**[cite: 9].

## 🚀 Funcionalidades

* **Painel do Servidor:** Abertura de requerimentos, anexação de arquivos comprobatórios (PDFs) e acompanhamento de status em tempo real.
* **Cálculo Automático:** Motor de regras de negócio que soma a pontuação e classifica o requerimento do Nível I ao VI com base nos Anexos do Decreto.
* **Painel da Comissão (CRSC-PCCTAE):** Área restrita para membros da comissão auditarem os memoriais, glosarem itens e emitirem pareceres fundamentados de deferimento ou indeferimento.
* **Geração de Dossiê PDF:** Mesclagem automática do Memorial Descritivo em HTML com todos os PDFs comprobatórios anexados pelo servidor, organizados por inciso e item da lei.

## 🛠️ Tecnologias Utilizadas

* Python 3.x
* Django 5.x
* Bootstrap 5 (Interface UI/UX)
* xhtml2pdf & pypdf (Geração e manipulação de relatórios PDF)
* SQLite (Banco de dados padrão para desenvolvimento)

## Licenciamento

*  Disponibilizado sob Licença Pública Geral GNU v3 (GPL-3) 

---

## ⚙️ Instruções de Instalação e Configuração

Siga os passos abaixo para rodar o projeto localmente em sua máquina.

### 1. Preparação do Ambiente
Clone este repositório e crie um ambiente virtual:

```bash
git clone https://github.com/fabionaves-max/rsccalc.git
cd rsccalc
python -m venv venv

# Ativando o ambiente virtual:
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale os requerimentos
pip install -r requirements.txt

#Criando o banco de dados
python manage.py makemigrations
python manage.py makemigrations main
python manage.py migrate

#Importando os critérios do decreto
python manage.py loaddata criterios.json

#Criar o super usuario
python manage.py createsuperuser

#Executar o servidor
python manage.py runserver

#Acesse o pagina de administração e adicione o servidor
http://localhost:8000/admin/

#Pronto o sistema estará pronto para ser utilizado em:
http://localhost:8000/

```

