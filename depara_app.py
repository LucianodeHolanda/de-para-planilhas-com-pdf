import streamlit as st
import pdfplumber
import pandas as pd
import json
import os
import difflib
from datetime import date, datetime
from io import BytesIO

st.set_page_config(page_title="Mapeamento de Colunas - DE PARA", layout="wide")

# Funções auxiliares
def caminho_arquivo(cliente_nome):
    return f"mapeamentos/{cliente_nome.strip().lower().replace(' ', '_')}_map.json"

def salvar_mapeamento(cliente_nome, mapeamento):
    os.makedirs("mapeamentos", exist_ok=True)
    with open(caminho_arquivo(cliente_nome), "w", encoding="utf-8") as f:
        json.dump(mapeamento, f, indent=2)

def carregar_mapeamento(cliente_nome):
    try:
        with open(caminho_arquivo(cliente_nome), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def carregar_clientes():
    if os.path.exists("clientes.json"):
        with open("clientes.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Verificação de login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.tipo_usuario = None
# Inicialização preventiva de variáveis
cliente_files = None
pdf_files = None
clientes_dados = []


if not st.session_state.autenticado:
    # Exibindo a logo
    st.image("Imagens/logo-de-para.png", width=180)


    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    clientes = carregar_clientes()
    if st.button("Entrar"):
        if usuario in clientes and clientes[usuario]["senha"] == senha:
            data_expiracao = datetime.strptime(clientes[usuario]["expira_em"], "%Y-%m-%d").date()
            if date.today() <= data_expiracao:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario
                st.session_state.tipo_usuario = "admin" if usuario == "admin" else "cliente"
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("⛔ Sua senha expirou. Entre em contato com o administrador.")
        else:
            st.error("❌ Usuário ou senha inválidos.")
    
    # Adicionando opção de redefinir senha
    st.subheader("🔑 Redefinir Senha")
    usuario_redefinir = st.text_input("Digite o seu nome de usuário para redefinir a senha")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar_senha = st.text_input("Confirme a Nova Senha", type="password")

    if st.button("Redefinir Senha"):
        if usuario_redefinir in clientes:
            if nova_senha == confirmar_senha:
                clientes[usuario_redefinir]["senha"] = nova_senha
                with open("clientes.json", "w", encoding="utf-8") as f:
                    json.dump(clientes, f, indent=2)
                st.success(f"✅ Senha do usuário '{usuario_redefinir}' redefinida com sucesso!")
            else:
                st.error("❌ As senhas não coincidem. Tente novamente.")
        else:
            st.error("❌ Usuário não encontrado.")
else:
    print("**** Entrou no bloco ELSE após o login ****")
    st.sidebar.write(f"👤 Usuário: `{st.session_state.usuario}`")
    # Botão para importar mapeamento salvo
    if st.session_state.tipo_usuario == "cliente":
        cliente_nome = st.session_state.usuario
        if st.button("📥 Importar mapeamento salvo"):
            mapeamento_salvo = carregar_mapeamento(cliente_nome)
            if mapeamento_salvo:
                st.session_state.mapeamento_carregado = mapeamento_salvo
                st.success("✅ Mapeamento carregado com sucesso!")
            else:
                st.warning("⚠️ Nenhum mapeamento salvo encontrado para este cliente.")

    if st.sidebar.button("🚪 Sair"):
        st.session_state.autenticado = False
        st.rerun()


    st.title("🗂️ Ferramenta DE-PARA de Planilhas")
    st.write("🚀 Faça o mapeamento entre sua planilha modelo e a planilha do cliente de forma visual e prática.")

    # Se for ADMIN, exibe painel para cadastrar e excluir usuários
    if st.session_state.tipo_usuario == "admin":
        with st.expander("🔐 Gerenciar Usuários (Apenas Admin)", expanded=False):
            clientes = carregar_clientes()
            
            
            tab1, tab2 = st.tabs(["➕ Cadastrar Novo", "❌ Excluir Usuário"])

            with tab1:
                novo_usuario = st.text_input("Novo usuário", key="novo_usuario")
                nova_senha = st.text_input("Senha", type="password", key="nova_senha")
                data_expiracao = st.date_input("Data de expiração", key="data_expiracao", value=date.today())
                if st.button("Cadastrar Usuário"):
                    if not novo_usuario or not nova_senha:
                        st.warning("⚠️ Usuário e senha são obrigatórios.")
                    elif novo_usuario in clientes:
                        st.error("❌ Esse usuário já existe.")
                    else:
                        clientes[novo_usuario] = {
                            "senha": nova_senha,
                            "expira_em": data_expiracao.strftime("%Y-%m-%d")
                        }
                        with open("clientes.json", "w", encoding="utf-8") as f:
                            json.dump(clientes, f, indent=2)
                        st.success(f"✅ Usuário '{novo_usuario}' cadastrado com sucesso!")

            with tab2:
                usuarios = [u for u in clientes.keys() if u != "admin"]
                usuario_excluir = st.selectbox("Selecione um usuário para excluir", options=usuarios)
                if st.button("Excluir Usuário"):
                    if usuario_excluir in clientes:
                        del clientes[usuario_excluir]
                        with open("clientes.json", "w", encoding="utf-8") as f:
                            json.dump(clientes, f, indent=2)
                        st.success(f"✅ Usuário '{usuario_excluir}' excluído com sucesso!")
                        st.rerun()

    # Campo de nome do cliente
    cliente_nome = st.text_input("🧾 Nome do Cliente (usado para salvar o mapeamento)", "")

    # Uploads
    modelo_file = st.file_uploader("1️⃣ Envie sua planilha modelo (com os nomes padrão)", type=["xlsx"])
    cliente_files = st.file_uploader("2️⃣ Envie as planilhas do cliente", type=["xlsx"], accept_multiple_files=True)  
    pdf_files = st.file_uploader("📄 Envie arquivos PDF para conversão", type=["pdf"], accept_multiple_files=True, key="pdf_files")
      



    modelo = cliente = None
    planilhas_cliente_nomes = []

    if modelo_file:
        try:
            modelo = pd.read_excel(modelo_file)
            st.success("✅ Planilha modelo carregada com sucesso!")
            st.dataframe(modelo.head())
        except Exception as e:
            st.error(f"Erro ao carregar a planilha modelo: {e}")


# Este bloco deve estar no nível base
if cliente_files:
    for uploaded_file in cliente_files:
        try:
            cliente_dado = pd.read_excel(uploaded_file)
            clientes_dados.append(cliente_dado)  # Adicionar os dados corretamente na lista
            planilhas_cliente_nomes.append(uploaded_file.name)
            st.success(f"✅ Planilha do cliente carregada: {uploaded_file.name}")
            st.dataframe(cliente_dado.head())
        except Exception as e:
            st.error(f"Erro ao carregar a planilha do cliente '{uploaded_file.name}': {e}")

# PASSO 3: Conversão e download dos PDFs
if pdf_files:
    for pdf_file in pdf_files:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                tabelas = []
                for page in pdf.pages:
                    for table in page.extract_tables():
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tabelas.append(df)

            if not tabelas:
                st.warning(f"⚠️ Nenhuma tabela detectada no PDF '{pdf_file.name}'.")
            else:
                st.success(f"✅ {len(tabelas)} tabela(s) extraída(s) do PDF '{pdf_file.name}'.")

                tabela_idx = 0
                if len(tabelas) > 1:
                    tabela_idx = st.selectbox(
                        f"🔢 Escolha qual tabela usar de '{pdf_file.name}'",
                        range(len(tabelas)),
                        format_func=lambda i: f"Tabela {i+1}",
                        key=f"select_{pdf_file.name}"
                    )

                df_pdf = tabelas[tabela_idx]
                st.dataframe(df_pdf.head())

                clientes_dados.append(df_pdf)
                planilhas_cliente_nomes.append(f"{pdf_file.name} (PDF convertido)")

                # Download do Excel gerado
                output = BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df_pdf.to_excel(writer, index=False, sheet_name="PDF Convertido")
                output.seek(0)

                st.download_button(
                    label=f"⬇️ Baixar Excel gerado de '{pdf_file.name}'",
                    data=output,
                    file_name=f"{pdf_file.name.replace('.pdf', '')}_convertido.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{pdf_file.name}"
                )

        except Exception as e:
            st.error(f"Erro ao processar o PDF '{pdf_file.name}': {e}")

    print(f"Valor de clientes_dados antes da condição de mapeamento: {clientes_dados}")
    print(f"Modelo carregado: {modelo is not None}")
    print(f"Nome do cliente preenchido: {cliente_nome.strip() != ''}")    


    # Mapeamento
    if modelo is not None and len(clientes_dados) > 0 and cliente_nome.strip():
        st.subheader("3️⃣ Mapeamento de Colunas")
        st.write("Associe as colunas da sua planilha modelo com as colunas das planilhas do cliente:")

        mapeamento_existente = carregar_mapeamento(cliente_nome)
        mapeamento = {}

        for col in modelo.columns:
            valor_padrao = mapeamento_existente.get(col, ("", ""))  # (planilha, coluna_cliente)
            planilha_padrao, coluna_padrao = valor_padrao

            # Seleciona qual planilha do cliente foi escolhida
            selected_planilha = st.selectbox(
                f"De qual planilha o valor de '{col}' vem?",
                options=[""] + planilhas_cliente_nomes,
                index=([""] + planilhas_cliente_nomes).index(planilha_padrao) if planilha_padrao in planilhas_cliente_nomes else 0,
                key=f"planilha_{col}"
    )

            if selected_planilha:
                index_cliente = planilhas_cliente_nomes.index(selected_planilha)
                cliente_selecionado = clientes_dados[index_cliente]
                colunas_cliente = cliente_selecionado.columns.tolist()
                # Calcula similaridade entre a coluna da planilha modelo e as colunas do cliente
                import difflib  # coloque isso no início do script, se ainda não tiver feito

                coluna_modelo_valores = modelo[col].astype(str)
                nome_coluna_modelo = col.lower()

                similaridades = {}
                for c in colunas_cliente:
                    try:
                        nome_coluna_cliente = c.lower()

                        # Similaridade entre nomes
                        sim_nome = difflib.SequenceMatcher(None, nome_coluna_modelo, nome_coluna_cliente).ratio()

                        # Similaridade entre valores (Jaccard)
                        coluna_cliente_valores = cliente_selecionado[c].astype(str)
                        set_modelo = set(coluna_modelo_valores.head(100))
                        set_cliente = set(coluna_cliente_valores.head(100))
                        intersecao = set_modelo & set_cliente
                        uniao = set_modelo | set_cliente
                        sim_valores = len(intersecao) / len(uniao) if uniao else 0

                        # Combinação com pesos (ajuste se quiser priorizar nomes ou valores)
                        peso_nome = 0.6
                        peso_valores = 0.4
                        similaridade_total = (peso_nome * sim_nome) + (peso_valores * sim_valores)

                        similaridades[c] = similaridade_total
                    except:
                        similaridades[c] = 0
                coluna_mais_similar = max(similaridades, key=similaridades.get)

                # Adiciona o emoji de destaque ⭐ à coluna mais similar
                colunas_para_mostrar = []
                for c in colunas_cliente:
                    if c == coluna_mais_similar:
                        colunas_para_mostrar.append(f"⭐ {c}")
                    else:
                        colunas_para_mostrar.append(c)


                # Seleciona qual coluna da planilha foi associada
                coluna_selecionada = st.selectbox(
                    f"Qual coluna da planilha '{selected_planilha}' corresponde a '{col}'?",
                    options=[""] + colunas_para_mostrar,
                    index=([""] + colunas_para_mostrar).index(f"⭐ {coluna_padrao}") if f"⭐ {coluna_padrao}" in colunas_para_mostrar else ([""] + colunas_para_mostrar).index(coluna_padrao) if coluna_padrao in colunas_para_mostrar else 0,
                    key=f"coluna_{col}"
        )

                if selected_planilha and coluna_selecionada:
                    coluna_limpa = coluna_selecionada.replace("⭐", "").strip()
                    mapeamento[col] = (selected_planilha, coluna_limpa)
                    st.success(f"✅ Coluna '{col}' associada a '{coluna_limpa}' da planilha '{selected_planilha}'")
        
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Salvar Mapeamento"):
                salvar_mapeamento(cliente_nome, mapeamento)
                st.success("✅ Mapeamento salvo com sucesso!")

        with col2:
            if st.button("🔁 Gerar Nova Planilha com Colunas Mapeadas"):
                novo_df = modelo.copy()
                for col, (planilha, coluna_cliente) in mapeamento.items():
                    index_cliente = planilhas_cliente_nomes.index(planilha)
                    cliente_selecionado = clientes_dados[index_cliente]
                    novo_df[col] = cliente_selecionado[coluna_cliente]
                output = BytesIO()
                novo_df.to_excel(output, index=False, engine='xlsxwriter')
                st.success("✅ Arquivo gerado com sucesso!")
                st.download_button("📥 Baixar Planilha Transformada", data=output.getvalue(), file_name="planilha_transformada.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    else:
        st.info("👆 Preencha o nome do cliente e envie a planilha modelo e as planilhas do cliente para iniciar o mapeamento.")
