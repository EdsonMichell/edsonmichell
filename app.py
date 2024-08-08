import streamlit as st
import pandas as pd
import os
import altair as alt

# Funções para carregar e salvar dados
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

def save_image(image, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(image.getbuffer())

# Inicialização dos dados
product_file = 'products.csv'
sales_file = 'sales.csv'
accounts_file = 'accounts.csv'
installments_file = 'installments.csv'

if 'products' not in st.session_state:
    st.session_state.products = load_data(product_file, ['Produto', 'Categoria', 'Preço de Compra', 'Preço de Venda', 'Quantidade', 'Conta', 'Foto'])
if 'sales' not in st.session_state:
    st.session_state.sales = load_data(sales_file, ['Produto', 'Quantidade', 'Preço de Venda', 'Cliente', 'Forma de Pagamento', 'Parcelas', 'Conta'])
if 'accounts' not in st.session_state:
    st.session_state.accounts = load_data(accounts_file, ['Conta', 'Saldo'])
if 'installments' not in st.session_state:
    st.session_state.installments = load_data(installments_file, ['Cliente', 'Produto', 'Valor', 'Prazo', 'Pago'])

# Função para calcular relatórios
def calcular_relatorios():
    total_gasto = (st.session_state.products['Preço de Compra'] * st.session_state.products['Quantidade']).sum()
    total_vendas = (st.session_state.sales['Preço de Venda'] * st.session_state.sales['Quantidade']).sum()
    total_estoque = (st.session_state.products['Preço de Venda'] * st.session_state.products['Quantidade']).sum()
    lucro = total_vendas - total_gasto
    return total_gasto, total_vendas, total_estoque, lucro

# Atualizar saldo das contas
def atualizar_saldo_conta(conta, valor):
    if conta in st.session_state.accounts['Conta'].values:
        st.session_state.accounts.loc[st.session_state.accounts['Conta'] == conta, 'Saldo'] += valor
    else:
        st.session_state.accounts = st.session_state.accounts.append({'Conta': conta, 'Saldo': valor}, ignore_index=True)
    save_data(st.session_state.accounts, accounts_file)

# Verificar saldo da conta
def verificar_saldo(conta, valor):
    saldo = st.session_state.accounts.loc[st.session_state.accounts['Conta'] == conta, 'Saldo'].values
    if saldo.size == 0:
        return False
    return saldo[0] >= valor

# Função de reset
def reset_program():
    st.session_state.products = pd.DataFrame(columns=['Produto', 'Categoria', 'Preço de Compra', 'Preço de Venda', 'Quantidade', 'Conta', 'Foto'])
    st.session_state.sales = pd.DataFrame(columns=['Produto', 'Quantidade', 'Preço de Venda', 'Cliente', 'Forma de Pagamento', 'Parcelas', 'Conta'])
    st.session_state.accounts = pd.DataFrame(columns=['Conta', 'Saldo'])
    st.session_state.installments = pd.DataFrame(columns=['Cliente', 'Produto', 'Valor', 'Prazo', 'Pago'])
    save_data(st.session_state.products, product_file)
    save_data(st.session_state.sales, sales_file)
    save_data(st.session_state.accounts, accounts_file)
    save_data(st.session_state.installments, installments_file)
    st.success("Programa resetado com sucesso!")

# Definindo a senha
PASSWORD = "1718"

# Função para autenticação
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True
    else:
        pwd = st.text_input("Digite a senha:", type="password")
        if pwd == PASSWORD:
            st.session_state.password_correct = True
            return True
        else:
            st.error("")
            return False

# Interface do aplicativo
if check_password():
    st.title("Loja de Roupas e Acessórios")

    # Botão para resetar o programa
    if st.sidebar.button("Resetar Programa"):
        reset_password = st.sidebar.text_input("Digite a senha para resetar:", type="password")
        if reset_password == PASSWORD:
            reset_program()
        else:
            st.sidebar.error("Senha incorreta para resetar o programa.")

    # Menu com botões
    menu = {
        "Cadastrar Produto": "cadastrar_produto",
        "Visualizar Inventário": "visualizar_inventario",
        "Registrar Venda": "registrar_venda",
        "Relatórios": "relatorios",
        "Contas": "contas",
        "Catálogo": "catalogo",
        "Gerenciador de Vendas a Prazo": "gerenciador_vendas_prazo",
        "Histórico de Transações": "historico_transacoes"
    }
    
    # Define a página inicial ou a selecionada
    if 'page' not in st.session_state:
        st.session_state.page = "registrar_venda"
    
    # Botões do menu
    for label, page in menu.items():
        if st.sidebar.button(label):
            st.session_state.page = page

    # Páginas
    page = st.session_state.page
    
    if page == "cadastrar_produto":
        st.subheader("Cadastrar Novo Produto")
        if st.session_state.accounts.empty:
            st.warning("Nenhuma conta cadastrada. Por favor, cadastre uma conta antes de adicionar produtos.")
            st.stop()
        with st.form(key='product_form'):
            produto = st.text_input("Nome do Produto")
            categoria = st.selectbox("Categoria", ["Roupas", "Acessórios para Celular"])
            preco_compra = st.number_input("Preço de Compra", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço de Venda", min_value=0.0, format="%.2f")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            conta_pagamento = st.selectbox("Conta Usada para Pagamento", st.session_state.accounts['Conta'].unique())
            foto = st.file_uploader("Carregar Foto do Produto", type=["png", "jpg", "jpeg"])
            submit_button = st.form_submit_button(label="Cadastrar")

            if submit_button:
                custo_total = preco_compra * quantidade
                if verificar_saldo(conta_pagamento, custo_total):
                    foto_path = None
                    if foto is not None:
                        foto_path = f"images/{produto}_{foto.name}"
                        save_image(foto, foto_path)
                    new_product = pd.DataFrame([[produto, categoria, preco_compra, preco_venda, quantidade, conta_pagamento, foto_path]],
                                               columns=['Produto', 'Categoria', 'Preço de Compra', 'Preço de Venda', 'Quantidade', 'Conta', 'Foto'])
                    st.session_state.products = pd.concat([st.session_state.products, new_product], ignore_index=True)
                    atualizar_saldo_conta(conta_pagamento, -custo_total)
                    save_data(st.session_state.products, product_file)
                    st.success("Produto cadastrado com sucesso!")
                else:
                    st.error("Saldo insuficiente na conta escolhida para pagamento!")

    elif page == "visualizar_inventario":
        st.subheader("Inventário de Produtos")
        if st.session_state.products['Quantidade'].sum() == 0:
            st.warning("Estoque está vazio. Cadastre mais produtos.")
            st.stop()
        busca_produto = st.text_input("Buscar Produto")
        produtos_filtrados = st.session_state.products[st.session_state.products['Produto'].str.contains(busca_produto, case=False, na=False)]
        
        if produtos_filtrados.empty:
            st.write("Nenhum produto encontrado.")
        else:
            st.dataframe(produtos_filtrados)
            
            # Formulário para editar um produto
            produto_para_editar = st.selectbox("Escolha um produto para editar", produtos_filtrados['Produto'].unique())
            produto_info = st.session_state.products[st.session_state.products['Produto'] == produto_para_editar].iloc[0]

            with st.form(key='edit_product_form'):
                produto = st.text_input("Nome do Produto", value=produto_info['Produto'])
                categoria = st.selectbox("Categoria", ["Roupas", "Acessórios para Celular"], index=["Roupas", "Acessórios para Celular"].index(produto_info['Categoria']))
                preco_compra = st.number_input("Preço de Compra", min_value=0.0, format="%.2f", value=produto_info['Preço de Compra'])
                preco_venda = st.number_input("Preço de Venda", min_value=0.0, format="%.2f", value=produto_info['Preço de Venda'])
                quantidade = st.number_input("Quantidade", min_value=1, step=1, value=produto_info['Quantidade'])
                conta_pagamento = st.selectbox("Conta Usada para Pagamento", st.session_state.accounts['Conta'].unique(), index=list(st.session_state.accounts['Conta'].unique()).index(produto_info['Conta']))
                foto = st.file_uploader("Carregar Foto do Produto", type=["png", "jpg", "jpeg"], key="foto_upload")
                submit_button = st.form_submit_button(label="Salvar Alterações")

                if submit_button:
                    if foto is not None:
                        foto_path = f"images/{produto}_{foto.name}"
                        save_image(foto, foto_path)
                    else:
                        foto_path = produto_info['Foto']
                    
                    st.session_state.products.loc[st.session_state.products['Produto'] == produto_para_editar] = [produto, categoria, preco_compra, preco_venda, quantidade, conta_pagamento, foto_path]
                    save_data(st.session_state.products, product_file)
                    st.success("Produto atualizado com sucesso!")
                    st.experimental_rerun() # Recarrega a página para atualizar a tabela com as alterações

    elif page == "registrar_venda":
        st.subheader("Registrar Venda de Produto")
        if st.session_state.products['Quantidade'].sum() == 0:
            st.warning("Estoque está vazio. Cadastre mais produtos.")
        else:
            with st.form(key='sales_form'):
                produto = st.selectbox("Produto", st.session_state.products['Produto'])
                quantidade_venda = st.number_input("Quantidade", min_value=1, step=1)
                cliente = st.text_input("Nome do Cliente")
                forma_pagamento = st.selectbox("Forma de Pagamento", ["Cartão", "Pix", "Dinheiro à vista", "Parcelado"])
                parcelas = st.number_input("Parcelas", min_value=1, step=1) if forma_pagamento == "Parcelado" else 1
                conta_recebimento = st.selectbox("Conta para Recebimento", st.session_state.accounts['Conta'].unique())
                submit_button = st.form_submit_button(label="Registrar Venda")

                if submit_button:
                    produto_info = st.session_state.products[st.session_state.products['Produto'] == produto].iloc[0]
                    if produto_info['Quantidade'] >= quantidade_venda:
                        preco_venda = produto_info['Preço de Venda']
                        nova_quantidade = produto_info['Quantidade'] - quantidade_venda
                        st.session_state.products.loc[st.session_state.products['Produto'] == produto, 'Quantidade'] = nova_quantidade

                        new_sale = pd.DataFrame([[produto, quantidade_venda, preco_venda, cliente, forma_pagamento, parcelas, conta_recebimento]],
                                                columns=['Produto', 'Quantidade', 'Preço de Venda', 'Cliente', 'Forma de Pagamento', 'Parcelas', 'Conta'])
                        st.session_state.sales = pd.concat([st.session_state.sales, new_sale], ignore_index=True)
                        atualizar_saldo_conta(conta_recebimento, preco_venda * quantidade_venda)
                        save_data(st.session_state.sales, sales_file)
                        save_data(st.session_state.products, product_file)
                        st.success("Venda registrada com sucesso!")

                        if forma_pagamento == "Pix":
                            st.image("images/pix.jpg", caption="Pagamento via Pix")
                    else:
                        st.error("Quantidade insuficiente em estoque!")

    elif page == "relatorios":
        st.subheader("Relatórios")
        total_gasto, total_vendas, total_estoque, lucro = calcular_relatorios()
        st.write(f"Total gasto em compras: R$ {total_gasto:.2f}")
        st.write(f"Total de vendas: R$ {total_vendas:.2f}")
        st.write(f"Valor total em estoque: R$ {total_estoque:.2f}")
        st.write(f"Lucro: R$ {lucro:.2f}")
        
        # Adicionar gráfico de vendas
        vendas_por_produto = st.session_state.sales.groupby('Produto')['Quantidade'].sum().reset_index()
        grafico_vendas = alt.Chart(vendas_por_produto).mark_bar().encode(
            x='Produto',
            y='Quantidade'
        )
        st.altair_chart(grafico_vendas, use_container_width=True)

    elif page == "contas":
        st.subheader("Contas com Saldo Atual")
        st.dataframe(st.session_state.accounts)
        with st.form(key='account_form'):
            conta = st.text_input("Nome da Conta")
            saldo_inicial = st.number_input("Saldo Inicial", min_value=0.0, format="%.2f")
            submit_button = st.form_submit_button(label="Adicionar Conta")

            if submit_button:
                if conta in st.session_state.accounts['Conta'].values:
                    st.error("Conta já existente.")
                else:
                    new_account = pd.DataFrame([[conta, saldo_inicial]], columns=['Conta', 'Saldo'])
                    st.session_state.accounts = pd.concat([st.session_state.accounts, new_account], ignore_index=True)
                    save_data(st.session_state.accounts, accounts_file)
                    st.success("Conta adicionada com sucesso!")

    elif page == "catalogo":
        st.subheader("Catálogo de Produtos")
        for index, row in st.session_state.products.iterrows():
            st.image(row['Foto'], caption=row['Produto']) if row['Foto'] else st.write(row['Produto'])
            st.write(f"Preço: R$ {row['Preço de Venda']:.2f}")
            st.write(f"Quantidade em estoque: {row['Quantidade']}")

    elif page == "gerenciador_vendas_prazo":
        st.subheader("Gerenciador de Vendas a Prazo")
        st.dataframe(st.session_state.installments)
        with st.form(key='installment_form'):
            cliente = st.text_input("Nome do Cliente")
            produto = st.selectbox("Produto", st.session_state.products['Produto'])
            valor = st.number_input("Valor da Venda", min_value=0.0, format="%.2f")
            prazo = st.date_input("Prazo para Pagamento")
            submit_button = st.form_submit_button(label="Registrar Venda a Prazo")

            if submit_button:
                new_installment = pd.DataFrame([[cliente, produto, valor, prazo, False]],
                                               columns=['Cliente', 'Produto', 'Valor', 'Prazo', 'Pago'])
                st.session_state.installments = pd.concat([st.session_state.installments, new_installment], ignore_index=True)
                save_data(st.session_state.installments, installments_file)
                st.success("Venda a prazo registrada com sucesso!")

    elif page == "historico_transacoes":
        st.subheader("Histórico de Transações")
        st.dataframe(st.session_state.sales)
