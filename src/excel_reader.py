import pandas as pd
import os

def read_scale_excel(file_path, sheet_name='FEVEREIRO'): # Adicionei sheet_name como parâmetro
    """
    Lê um ficheiro Excel de escala de trabalho e tenta extrair os dados relevantes.
    Esta função precisará de ser adaptada à estrutura EXATA dos Excel do cliente.
    """
    try:
        # Tenta ler a folha especificada. Se não existir, tenta a primeira folha.
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, skiprows=0) # Começa com skiprows=0 para ver tudo
    except ValueError:
        print(f"Aviso: Folha '{sheet_name}' não encontrada em {file_path}. Tentando ler a primeira folha.")
        df = pd.read_excel(file_path, header=None, skiprows=0) # Tenta a primeira folha

    # --- AQUI COMEÇA A TUA ADAPTAÇÃO CRÍTICA ---
    # A. Identificar a linha do cabeçalho (onde estão "DIAS", "NOME", "FUNÇÃO", "1", "2", ...)
    #    Podes ter de procurar por palavras-chave como "DIAS" ou "NOME".
    header_row_index = -1
    for r_idx, row_data in df.iterrows():
        if 'DIAS' in row_data.values or 'NOME' in row_data.values:
            header_row_index = r_idx
            break

    if header_row_index == -1:
        print("Erro: Não foi possível encontrar a linha do cabeçalho. Por favor, verifique a estrutura do Excel.")
        return pd.DataFrame() # Retorna um DataFrame vazio se não encontrar o cabeçalho

    # Define o cabeçalho do DataFrame a partir da linha identificada
    # E ignora as linhas acima
    df.columns = df.iloc[header_row_index]
    df = df[header_row_index + 1:].reset_index(drop=True)

    # B. Tratar células unidas (merged cells) para as colunas de identificação (NOME, FUNÇÃO)
    #    Se os nomes e funções se repetem, mas só aparecem na primeira linha de um bloco de células unidas.
    #    Exemplo: df['NOME'] = df['NOME'].fillna(method='ffill')
    #    Vais ter de identificar os nomes corretos das colunas depois de definir o cabeçalho.

    # C. Identificar e Renomear Colunas Relevantes
    #    Normalmente, terás colunas para "NOME", "FUNÇÃO", e colunas para os dias "1", "2", ..., "31".
    #    Pode ser necessário renomear colunas que o pandas leu como números ou NaN.
    #    Exemplo (ajusta os nomes das colunas conforme o teu Excel):
    #    df = df.rename(columns={df.columns[0]: 'NOME', df.columns[1]: 'FUNCAO'})

    # D. Filtrar Linhas Irrelevantes (Totais, Médias, etc.)
    #    Podes ter linhas de totais ou médias que não são colaboradores.
    #    Exemplo: df = df[df['FUNÇÃO'].isin(['CT', 'CE', 'OPS'])] # Filtra por funções válidas
    #    Ou: df = df.dropna(subset=['NOME']) # Remove linhas sem nome

    # E. Selecionar apenas as colunas dos dias (1 a 31) e as de identificação
    #    Pode ser necessário converter os nomes das colunas de dias para string se forem números.
    #    daily_cols = [str(i) for i in range(1, 32)]
    #    df = df[['NOME', 'FUNÇÃO'] + daily_cols] # Exemplo

    return df

# Para testar este ficheiro individualmente, podes adicionar isto no final:
if __name__ == "__main__":
    # Certifica-te que tens um ficheiro de exemplo aqui: data/input/escala_fev_2025.xlsx
    # Altera o nome do ficheiro e da folha se necessário para o teu teste.
    example_file = os.path.join('data', 'input', 'escala_fev_2025.xlsx')
    target_sheet = 'FEVEREIRO' # Ou o nome da folha que queres ler

    if os.path.exists(example_file):
        print(f"A ler ficheiro: {example_file}, folha: {target_sheet}")
        scale_data = read_scale_excel(example_file, sheet_name=target_sheet)

        if not scale_data.empty:
            print("\nPrimeiras 5 linhas do DataFrame após leitura e cabeçalho:")
            print(scale_data.head())
            print("\nInformações do DataFrame:")
            print(scale_data.info())
            print("\nColunas do DataFrame:")
            print(scale_data.columns.tolist()) # Para ver os nomes das colunas
        else:
            print("DataFrame vazio. Verifique os logs de erro acima.")
    else:
        print(f"Erro: Ficheiro não encontrado em {example_file}. Certifica-te que o colocaste lá.")
