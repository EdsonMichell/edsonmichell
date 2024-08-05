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

    menu = ["Cadastrar Produto", "Visualizar Inventário", "Registrar Venda", "Relatórios", "Contas", "Catálogo", "Gerenciador de Vendas a Prazo", "Histórico de Transações"]
    choice = st.sidebar.selectbox("Menu", menu, index=3)

    if choice == "Cadastrar Produto":
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

    elif choice == "Visualizar Inventário":
        st.subheader("Inventário de Produtos")
        if st.session_state.products['Quantidade'].sum() == 0:
            st.warning("Estoque está vazio. Cadastre mais produtos.")
            st.stop()
        busca_produto = st.text_input("Buscar Produto")
        produtos_filtrados = st.session_state.products[
            st.session_state.products['Produto'].str.contains(busca_produto, case=False, na=False)]
        if produtos_filtrados.empty:
            st.write("Nenhum produto encontrado.")
        else:
            st.dataframe(produtos_filtrados)
            for i, row in produtos_filtrados.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{row['Produto']} - {row['Categoria']}")
                with col2:
                    if st.button('Editar', key=f"edit_{i}"):
                        st.write("Implementar funcionalidade de edição aqui.")
                with col3:
                    if st.button('Excluir', key=f"delete_{i}"):
                        st.session_state.products.drop(index=i, inplace=True)
                        save_data(st.session_state.products, product_file)
                        st.success("Produto excluído com sucesso!")

    elif choice == "Registrar Venda":
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

    elif choice == "Relatórios":
        st.subheader("Relatórios Detalhados")
        total_gasto, total_vendas, total_estoque, lucro = calcular_relatorios()
        st.write(f"**Total Gasto com Compras:** R${total_gasto:.2f}")
        st.write(f"**Total em Vendas:** R${total_vendas:.2f}")
        st.write(f"**Valor em Estoque:** R${total_estoque:.2f}")
        st.write(f"**Lucro:** R${lucro:.2f}")

        st.subheader("Resumo de Vendas")
        df_sales_summary = st.session_state.sales.groupby('Produto').agg(
            Quantidade_Vendida=('Quantidade', 'sum'),
            Total_Vendido=('Preço de Venda', 'sum')).reset_index()
        st.dataframe(df_sales_summary)

        st.subheader("Estoque Atual")
        df_inventory = st.session_state.products[['Produto', 'Quantidade', 'Preço de Venda']]
        st.dataframe(df_inventory)

        st.subheader("Gráficos")
        st.write("### Gráfico de Vendas por Produto")
        chart = alt.Chart(st.session_state.sales).mark_bar().encode(
            x='Produto',
            y='sum(Quantidade)',
            color='Produto'
        ).properties(width=600, height=400)
        st.altair_chart(chart)

        st.write("### Gráfico de Estoque por Produto")
        chart = alt.Chart(st.session_state.products).mark_bar().encode(
            x='Produto',
            y='Quantidade',
            color='Produto'
        ).properties(width=600, height=400)
        st.altair_chart(chart)

    elif choice == "Contas":
        st.subheader("Cadastrar Contas")
        with st.form(key='account_form'):
            conta = st.text_input("Nome da Conta")
            saldo_inicial = st.number_input("Saldo Inicial", min_value=0.0, format="%.2f")
            submit_button = st.form_submit_button(label="Adicionar Conta")
            if submit_button:
                if conta not in st.session_state.accounts['Conta'].values:
                    new_account = pd.DataFrame([[conta, saldo_inicial]], columns=['Conta', 'Saldo'])
                    st.session_state.accounts = pd.concat([st.session_state.accounts, new_account], ignore_index=True)
                    save_data(st.session_state.accounts, accounts_file)
                    st.success("Conta adicionada com sucesso!")
                else:
                    st.error("Conta já existente!")
        st.subheader("Contas Cadastradas")
        st.dataframe(st.session_state.accounts)

    elif choice == "Catálogo":
        st.subheader("Catálogo de Produtos")
        if st.session_state.products.empty:
            st.write("Nenhum produto cadastrado.")
        else:
            for _, row in st.session_state.products.iterrows():
                if pd.notna(row['Foto']):
                    st.image(row['Foto'], width=150)
                st.write(f"**Nome do Produto:** {row['Produto']}")
                st.write(f"**Preço de Venda:** R${row['Preço de Venda']:.2f}")
                st.write(f"**Quantidade no Estoque:** {row['Quantidade']}")
                st.markdown("---")

    elif choice == "Gerenciador de Vendas a Prazo":
        st.subheader("Gerenciar Vendas a Prazo")
        if st.session_state.sales.empty:
            st.write("Nenhuma venda a prazo efetuada.")
        with st.form(key='installment_form'):
            cliente = st.selectbox("Cliente", st.session_state.sales['Cliente'].unique())
            produto = st.selectbox("Produto", st.session_state.sales['Produto'].unique())
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            prazo = st.number_input("Prazo", min_value=1, step=1)
            submit_button = st.form_submit_button(label="Registrar Venda a Prazo")
            if submit_button:
                new_installment = pd.DataFrame([[cliente, produto, valor, prazo, False]], columns=['Cliente', 'Produto', 'Valor', 'Prazo', 'Pago'])
                st.session_state.installments = pd.concat([st.session_state.installments, new_installment], ignore_index=True)
                save_data(st.session_state.installments, installments_file)
                st.success("Venda a prazo registrada com sucesso!")
        st.subheader("Relatório de Vendas a Prazo")
        st.dataframe(st.session_state.installments[st.session_state.installments['Pago'] == False])

    elif choice == "Histórico de Transações":
        st.subheader("Histórico de Transações")
        st.dataframe(st.session_state.sales)

    # Notificações de estoque baixo
    st.sidebar.subheader("Notificações")
    estoque_baixo = st.session_state.products[st.session_state.products['Quantidade'] < 5]
    if not estoque_baixo.empty:
        st.sidebar.warning("Produtos com estoque baixo:")
        for i, row in estoque_baixo.iterrows():
            st.sidebar.write(f"{row['Produto']}: {row['Quantidade']} unidades")
    else:
        st.sidebar.write("Nenhum produto com estoque baixo.")
