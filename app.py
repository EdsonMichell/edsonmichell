import streamlit as st
import pandas as pd
import os


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

st.session_state.products = load_data(product_file,
                                      ['Produto', 'Categoria', 'Preço de Compra', 'Preço de Venda', 'Quantidade',
                                       'Conta', 'Foto'])
st.session_state.sales = load_data(sales_file,
                                   ['Produto', 'Quantidade', 'Preço de Venda', 'Cliente', 'Forma de Pagamento',
                                    'Parcelas', 'Conta'])
st.session_state.accounts = load_data(accounts_file, ['Conta', 'Saldo'])
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
        st.session_state.accounts = st.session_state.accounts.append({'Conta': conta, 'Saldo': valor},
                                                                     ignore_index=True)
    save_data(st.session_state.accounts, accounts_file)


# Verificar saldo da conta
def verificar_saldo(conta, valor):
    saldo = st.session_state.accounts.loc[st.session_state.accounts['Conta'] == conta, 'Saldo'].values
    if saldo.size == 0:
        return False
    return saldo[0] >= valor


# Interface do aplicativo
st.title("Gerenciamento de Loja de Roupas e Acessórios")

menu = ["Cadastrar Produto", "Visualizar Inventário", "Registrar Venda", "Relatórios", "Contas com Saldo Atual",
        "Catálogo", "Gerenciador de Vendas a Prazo"]
choice = st.sidebar.selectbox("Menu", menu, index=2)

# Cadastro de Produto
if choice == "Cadastrar Produto":
    st.subheader("Cadastrar Novo Produto")
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
                new_product = pd.DataFrame(
                    [[produto, categoria, preco_compra, preco_venda, quantidade, conta_pagamento, foto_path]],
                    columns=['Produto', 'Categoria', 'Preço de Compra', 'Preço de Venda', 'Quantidade', 'Conta',
                             'Foto'])
                st.session_state.products = pd.concat([st.session_state.products, new_product], ignore_index=True)
                atualizar_saldo_conta(conta_pagamento, -custo_total)
                save_data(st.session_state.products, product_file)
                st.success("Produto cadastrado com sucesso!")
            else:
                st.error("Saldo insuficiente na conta escolhida para pagamento!")

# Visualização de Inventário
elif choice == "Visualizar Inventário":
    st.subheader("Inventário de Produtos")
    st.dataframe(st.session_state.products)

# Registrar Venda
elif choice == "Registrar Venda":
    st.subheader("Registrar Venda de Produto")
    with st.form(key='sale_form'):
        produto_venda = st.selectbox("Produto", st.session_state.products['Produto'].unique())
        quantidade_venda = st.number_input("Quantidade Vendida", min_value=1, step=1)
        cliente = st.text_input("Nome do Cliente")
        forma_pagamento = st.selectbox("Forma de Pagamento", ["Cartão", "Pix", "Dinheiro à Vista", "Parcelado"])

        parcelas = 1
        if forma_pagamento == "Parcelado":
            parcelas = st.number_input("Quantidade de Parcelas", min_value=1, step=1)

        conta_recebimento = st.selectbox("Conta para Recebimento", st.session_state.accounts['Conta'].unique())

        submit_button = st.form_submit_button(label="Registrar Venda")

        if submit_button:
            idx = st.session_state.products[st.session_state.products['Produto'] == produto_venda].index[0]
            if st.session_state.products.at[idx, 'Quantidade'] >= quantidade_venda:
                st.session_state.products.at[idx, 'Quantidade'] -= quantidade_venda
                preco_venda = st.session_state.products.at[idx, 'Preço de Venda']
                new_sale = pd.DataFrame([[produto_venda, quantidade_venda, preco_venda, cliente, forma_pagamento,
                                          parcelas, conta_recebimento]],
                                        columns=['Produto', 'Quantidade', 'Preço de Venda', 'Cliente',
                                                 'Forma de Pagamento', 'Parcelas', 'Conta'])
                st.session_state.sales = pd.concat([st.session_state.sales, new_sale], ignore_index=True)
                atualizar_saldo_conta(conta_recebimento, preco_venda * quantidade_venda)
                save_data(st.session_state.sales, sales_file)
                save_data(st.session_state.products, product_file)
                st.success("Venda registrada com sucesso!")

                # Mostrar imagem se a forma de pagamento for Pix
                if forma_pagamento == "Pix":
                    st.image("images/pix.jpg", caption="Pagamento via Pix")

            else:
                st.error("Quantidade insuficiente em estoque!")

# Relatórios
elif choice == "Relatórios":
    st.subheader("Relatórios Detalhados")
    total_gasto, total_vendas, total_estoque, lucro = calcular_relatorios()

    st.write(f"**Total Gasto com Compras:** R${total_gasto:.2f}")
    st.write(f"**Total em Vendas:** R${total_vendas:.2f}")
    st.write(f"**Valor em Estoque:** R${total_estoque:.2f}")
    st.write(f"**Lucro:** R${lucro:.2f}")

    st.subheader("Detalhes das Vendas")
    st.dataframe(st.session_state.sales)

# Contas com Saldo Atual
elif choice == "Contas com Saldo Atual":
    st.subheader("Contas com Saldo Atual")
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

    st.subheader("Relatório de Contas")
    st.dataframe(st.session_state.accounts)

# Catálogo de Produtos
elif choice == "Catálogo":
    st.subheader("Catálogo de Produtos")
    for _, row in st.session_state.products.iterrows():
        if pd.notna(row['Foto']):
            st.image(row['Foto'], width=150)
        st.write(f"**Nome do Produto:** {row['Produto']}")
        st.write(f"**Preço de Venda:** R${row['Preço de Venda']:.2f}")
        st.write(f"**Quantidade no Estoque:** {row['Quantidade']}")
        st.markdown("---")

# Gerenciador de Vendas a Prazo
elif choice == "Gerenciador de Vendas a Prazo":
    st.subheader("Gerenciar Vendas a Prazo")
    with st.form(key='installment_form'):
        cliente = st.text_input("Nome do Cliente")
        produto = st.selectbox("Produto", st.session_state.products['Produto'].unique())
        valor = st.number_input("Valor da Venda", min_value=0.0, format="%.2f")
        prazo = st.selectbox("Prazo de Pagamento",
                             ["2 vezes", "3 vezes", "4 vezes", "5 vezes", "6 vezes", "Mais de 6 vezes"])
        pago = st.checkbox("Venda já paga?")
        submit_button = st.form_submit_button(label="Registrar Venda a Prazo")

        if submit_button:
            new_installment = pd.DataFrame([[cliente, produto, valor, prazo, pago]],
                                           columns=['Cliente', 'Produto', 'Valor', 'Prazo', 'Pago'])
            st.session_state.installments = pd.concat([st.session_state.installments, new_installment],
                                                      ignore_index=True)
            save_data(st.session_state.installments, installments_file)
            st.success("Venda a prazo registrada com sucesso!")

    st.subheader("Relatório de Vendas a Prazo")
    vendas_a_prazo = st.session_state.installments
    vendas_a_prazo = vendas_a_prazo[vendas_a_prazo['Pago'] == False]  # Exclui vendas já pagas
    st.dataframe(vendas_a_prazo)
