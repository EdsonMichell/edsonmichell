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

def reset_program(password):
    # Senha de confirmação para resetar
    if password == 'senha_secreta':  # Substitua 'senha_secreta' pela senha desejada
        # Apagar todos os arquivos de dados
        for file in [product_file, sales_file, accounts_file, installments_file]:
            if os.path.exists(file):
                os.remove(file)
        st.success("Programa resetado com sucesso!")
        st.experimental_rerun()
    else:
        st.error("Senha incorreta!")

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

# Botão de Resetar Programa
if st.sidebar.button("Resetar Programa"):
    senha = st.text_input("Digite a senha para confirmar o reset", type="password", key="reset_password")
    if st.button("Resetar Programa", key="reset_program"):
        reset_program(senha)

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
    df = st.session_state.products.copy()
    edited_rows = []
    
    for idx, row in df.iterrows():
        st.write(f"**Nome do Produto:** {row['Produto']}")
        st.write(f"**Categoria:** {row['Categoria']}")
        st.write(f"**Preço de Compra:** R${row['Preço de Compra']:.2f}")
        st.write(f"**Preço de Venda:** R${row['Preço de Venda']:.2f}")
        st.write(f"**Quantidade:** {row['Quantidade']}")
        st.write(f"**Conta:** {row['Conta']}")
        if row['Foto']:
            st.image(row['Foto'], width=150)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button(f"Editar {row['Produto']}", key=f"edit_{idx}"):
                edited_rows.append(idx)
        
        with col2:
            if st.button(f"Excluir {row['Produto']}", key=f"delete_{idx}"):
                st.session_state.products = st.session_state.products.drop(idx).reset_index(drop=True)
                save_data(st.session_state.products, product_file)
                st.success(f"Produto {row['Produto']} excluído com sucesso!")
                st.experimental_rerun()
    
    if edited_rows:
        for idx in edited_rows:
            row = df.iloc[idx]
            with st.form(key=f'edit_form_{idx}'):
                st.write(f"**Editando Produto:** {row['Produto']}")
                produto = st.text_input("Nome do Produto", value=row['Produto'])
                categoria = st.selectbox("Categoria", ["Roupas", "Acessórios para Celular"], index=["Roupas", "Acessórios para Celular"].index(row['Categoria']))
                preco_compra = st.number_input("Preço de Compra", min_value=0.0, format="%.2f", value=row['Preço de Compra'])
                preco_venda = st.number_input("Preço de Venda", min_value=0.0, format="%.2f", value=row['Preço de Venda'])
                quantidade = st.number_input("Quantidade", min_value=1, step=1, value=row['Quantidade'])
                conta_pagamento = st.selectbox("Conta Usada para Pagamento", st.session_state.accounts['Conta'].unique(), index=st.session_state.accounts['Conta'].tolist().index(row['Conta']))
                foto = st.file_uploader("Carregar Foto do Produto", type=["png", "jpg", "jpeg"], key=f"foto_{idx}")
                submit_button = st.form_submit_button(label="Atualizar")
                
                if submit_button:
                    foto_path = row['Foto']
                    if foto is not None:
                        foto_path = f"images/{produto}_{foto.name}"
                        save_image(foto, foto_path)
                    
                    st.session_state.products.at[idx, 'Produto'] = produto
                    st.session_state.products.at[idx, 'Categoria'] = categoria
                    st.session_state.products.at[idx, 'Preço de Compra'] = preco_compra
                    st.session_state.products.at[idx, 'Preço de Venda'] = preco_venda
                    st.session_state.products.at[idx, 'Quantidade'] = quantidade
                    st.session_state.products.at[idx, 'Conta'] = conta_pagamento
                    st.session_state.products.at[idx, 'Foto'] = foto_path
                    
                    save_data(st.session_state.products, product_file)
                    st.success("Produto atualizado com sucesso!")
                    st.experimental_rerun()

# Registrar Venda
elif choice == "Registrar Venda":
    st.subheader("Registrar Venda de Produto")
    if st.session_state.products['Quantidade'].sum() == 0:
        st.write("Não há produtos em estoque.")
        st.write("[Clique aqui para cadastrar novos produtos](#Cadastrar-Produto)")
    else:
        with st.form(key='sale_form'):
            produtos = st.session_state.products['Produto'].tolist()
            produto = st.selectbox("Produto", produtos)
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            cliente = st.text_input("Nome do Cliente")
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro à vista", "Cartão", "Pix", "Parcelado"])
            parcelas = st.number_input("Número de Parcelas", min_value=1, step=1) if forma_pagamento == "Parcelado" else 0
            conta = st.selectbox("Conta Recebida", st.session_state.accounts['Conta'].unique())
            submit_button = st.form_submit_button(label="Registrar Venda")

            if submit_button:
                # Validar quantidade em estoque
                produto_info = st.session_state.products[st.session_state.products['Produto'] == produto].iloc[0]
                if quantidade > produto_info['Quantidade']:
                    st.error("Quantidade solicitada é maior do que a disponível em estoque.")
                else:
                    # Atualizar estoque e registrar venda
                    preco_venda = produto_info['Preço de Venda']
                    valor_total = preco_venda * quantidade
                    st.session_state.products.loc[st.session_state.products['Produto'] == produto, 'Quantidade'] -= quantidade
                    st.session_state.sales = st.session_state.sales.append(
                        {'Produto': produto, 'Quantidade': quantidade, 'Preço de Venda': preco_venda, 'Cliente': cliente,
                         'Forma de Pagamento': forma_pagamento, 'Parcelas': parcelas, 'Conta': conta},
                        ignore_index=True)
                    atualizar_saldo_conta(conta, valor_total)
                    save_data(st.session_state.products, product_file)
                    save_data(st.session_state.sales, sales_file)
                    st.success("Venda registrada com sucesso!")

# Relatórios
elif choice == "Relatórios":
    st.subheader("Relatórios de Vendas e Compras")
    total_gasto, total_vendas, total_estoque, lucro = calcular_relatorios()
    st.write(f"**Total Gasto com Compras:** R${total_gasto:.2f}")
    st.write(f"**Total de Vendas:** R${total_vendas:.2f}")
    st.write(f"**Valor Total em Estoque:** R${total_estoque:.2f}")
    st.write(f"**Lucro:** R${lucro:.2f}")

# Contas com Saldo Atual
elif choice == "Contas com Saldo Atual":
    st.subheader("Contas com Saldo Atual")
    st.write(st.session_state.accounts)

# Catálogo
elif choice == "Catálogo":
    st.subheader("Catálogo de Produtos")
    st.write(st.session_state.products[['Produto', 'Foto', 'Preço de Venda', 'Quantidade']])
    
# Gerenciador de Vendas a Prazo
elif choice == "Gerenciador de Vendas a Prazo":
    st.subheader("Gerenciador de Vendas a Prazo")
    st.write(st.session_state.installments)

