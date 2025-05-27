import pandas as pd
import os
import json

# --- FUNÇÃO PARA CARREGAR AS REGRAS ---
def load_turn_rules(config_path):
    """
    Carrega as regras de duração dos turnos e outras configurações
    de um ficheiro JSON.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: O ficheiro de configuração '{config_path}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O ficheiro de configuração '{config_path}' não é um JSON válido.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o ficheiro de configuração '{config_path}': {e}")
        return None

# --- FUNÇÃO DE LEITURA DO EXCEL ---
def read_scale_excel(file_path, sheet_name=None):
    """
    Lê um ficheiro Excel de escala de trabalho diretamente, assumindo as colunas
    'Nome' e 'Funcao' pelas suas posições, e depois os dias.
    Esta é uma abordagem mais direta para o cabeçalho problemático.
    """
    try:
        # 1. Determinar o nome da folha
        if sheet_name:
            target_sheet = sheet_name
        else:
            excel_file = pd.ExcelFile(file_path)
            all_sheet_names = excel_file.sheet_names
            if not all_sheet_names:
                print(f"Erro: Nenhuma folha encontrada no ficheiro {file_path}.")
                return pd.DataFrame()
            target_sheet = all_sheet_names[0]
            print(f"Aviso: Nome da folha não especificado. Tentando ler a primeira folha: '{target_sheet}'.")

        # 2. Ler o DataFrame completo, ignorando todas as linhas de cabeçalho
        # Os dados dos colaboradores começam na linha 14 do Excel, ou seja, skiprows = 13.
        # Não especificamos 'header' para que o pandas leia as colunas como 0, 1, 2...
        df = pd.read_excel(file_path, sheet_name=target_sheet, skiprows=13, header=None)

        if df.empty:
            print(f"Aviso: O DataFrame lido da folha '{target_sheet}' em {file_path} está vazio após skiprows=13. Verifique o ficheiro ou o nome da folha.")
            return pd.DataFrame()

        # 3. Criar os novos nomes de colunas com base nas posições observadas
        # Assumimos que:
        # Coluna 0 (Unnamed_Col_0) é o 'Nome'
        # Coluna 1 (Unnamed_Col_1) é a 'Funcao'
        # As colunas seguintes são os dias (a partir do dia 1)
        
        num_cols = df.shape[1]
        
        new_column_names = []
        if num_cols > 0:
            new_column_names.append('Nome')
        if num_cols > 1:
            new_column_names.append('Funcao')
        
        for i in range(2, num_cols):
            if i - 1 <= 31: # Assume que os dias vão de 1 a 31
                 new_column_names.append(i - 1)
            else:
                 new_column_names.append(f'Extra_Col_{i}')
        
        df.columns = new_column_names

        # 4. Tratar células unidas (merged cells) para colunas de identificação (Nome, Funcao)
        if 'Nome' in df.columns:
            df['Nome'] = df['Nome'].ffill()
        if 'Funcao' in df.columns:
            df['Funcao'] = df['Funcao'].ffill()

        # 5. Remover linhas onde o 'Nome' é NaN
        if 'Nome' in df.columns:
            df = df.dropna(subset=['Nome']).reset_index(drop=True)
        else:
            print(f"Erro Crítico: A coluna 'Nome' não foi criada na folha '{target_sheet}'. Não é possível continuar o processamento.")
            return pd.DataFrame()

        # 5.1. Remover linhas com turnos a '0' ou vazias em todos os dias
        day_columns = [col for col in df.columns if isinstance(col, int) and 1 <= col <= 31] 
        
        if day_columns:
            temp_df_days = df[day_columns].fillna('')
            temp_df_days = temp_df_days.apply(lambda x: x.astype(str).replace('NAN', '0', regex=True).replace(r'^\s*$', '0', regex=True).str.strip().str.upper())
            
            all_zeros_mask = (temp_df_days == '0').all(axis=1)
            
            rows_before_filter = df.shape[0]
            df = df[~all_zeros_mask].reset_index(drop=True)
            rows_after_filter = df.shape[0]
            if (rows_before_filter - rows_after_filter) > 0:
                print(f"Informação: Removidas {rows_before_filter - rows_after_filter} linhas com turnos a '0' ou vazias em todos os dias na folha '{target_sheet}'.")

        # 6. Converter colunas de dias para strings (garantir que turnos como 'D', 'N', '0' são tratados como texto)
        day_columns = [col for col in df.columns if isinstance(col, int) and 1 <= col <= 31]
        for col in day_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()

        # 7. Reorganizar as colunas
        final_desired_order = []
        if 'Nome' in df.columns: final_desired_order.append('Nome')
        if 'Funcao' in df.columns: final_desired_order.append('Funcao')
        
        sorted_day_columns = sorted([col for col in day_columns if col in df.columns])
        final_desired_order.extend(sorted_day_columns)

        other_columns = [col for col in df.columns if col not in final_desired_order]
        final_desired_order.extend(other_columns)

        df = df[[col for col in final_desired_order if col in df.columns]]

        return df

    except Exception as e:
        print(f"Erro ao ler ou processar o ficheiro Excel {file_path}, folha '{sheet_name}': {e}")
        return pd.DataFrame()

# --- FUNÇÃO DE PROCESSAMENTO DE DADOS E CÁLCULO DE HORAS ---
def process_scale_data(df, year, month, turn_rules):
    """
    Transforma o DataFrame da escala de trabalho para um formato de lista de turnos diários
    e calcula as horas.
    """
    if df.empty:
        return pd.DataFrame()

    processed_data = []
    
    day_columns = [col for col in df.columns if isinstance(col, int) and 1 <= col <= 31]

    turn_durations = turn_rules.get("turn_durations_hours", {})
    
    for index, row in df.iterrows():
        nome = row['Nome']
        funcao = row['Funcao']

        for day_num in day_columns:
            try:
                # Obter o número de dias no mês para evitar ValueErrors para dias inexistentes
                _, num_days_in_month = pd.Period(f'{year}-{month}', freq='M').days_in_month, pd.Period(f'{year}-{month}', freq='M').days_in_month
                if day_num > num_days_in_month:
                    continue # Ignorar dias que não existem no mês (ex: dia 30 em Fev)

                current_date = pd.Timestamp(year=year, month=month, day=day_num)
            except ValueError: # Este erro agora deve ser mais raro com a verificação de num_days_in_month
                continue 
            
            turno_raw = str(row[day_num]).strip().upper()

            horas_trabalhadas = turn_durations.get(turno_raw, 0)

            tipo_turno = 'OUTRO_NAO_CLASSIFICADO'
            if turno_raw == '0' or pd.isna(turno_raw) or turno_raw == '':
                tipo_turno = 'NAO_TRABALHADO'
            elif turno_raw == 'D':
                tipo_turno = 'DIA'
            elif turno_raw == 'N':
                tipo_turno = 'NOITE'
            elif turno_raw == 'DT':
                tipo_turno = 'DIA_TROCA'
            elif turno_raw == 'NT':
                tipo_turno = 'NOITE_TROCA'
            elif turno_raw == 'T':
                tipo_turno = 'TARDE_TROCA' 
            elif turno_raw == 'SA':
                tipo_turno = 'ADMINISTRATIVO_SA'
            elif turno_raw == 'SAT':
                tipo_turno = 'ADMINISTRATIVO_NO_TURNO'
            elif turno_raw == 'DTS':
                tipo_turno = 'DIA_TRABALHO_SUPLEMENTAR'
            elif turno_raw == 'NTS':
                tipo_turno = 'NOITE_TRABALHO_SUPLEMENTAR'
            elif turno_raw == 'FE':
                tipo_turno = 'FERIAS'
            elif turno_raw == 'L':
                tipo_turno = 'LICENCA'
            elif turno_raw == 'B':
                tipo_turno = 'BAIXA'
            elif turno_raw == 'FI':
                tipo_turno = 'FALTA_INJUSTIFICADA'
            elif turno_raw == 'FJ':
                tipo_turno = 'FALTA_JUSTIFICADA'
            elif turno_raw == 'DISP':
                tipo_turno = 'DISPENSA'
            elif turno_raw == 'FOTS':
                tipo_turno = 'FOLGA_OBRIGATORIA_SUPLEMENTAR'
            elif turno_raw == 'DTS5S':
                tipo_turno = 'DTS5S_ESPECIFICO'
            elif turno_raw == 'NTSS5S':
                tipo_turno = 'NTSS5S_ESPECIFICO'
            elif turno_raw == 'DTSDS':
                tipo_turno = 'DTSDS_ESPECIFICO'
            elif turno_raw == 'NTSDS':
                tipo_turno = 'NTSDS_ESPECIFICO'
            
            # --- Cálculo de Horas Normais, Extra, FOTS para o dia ---
            horas_normais = 0
            horas_extra = 0
            horas_fots = 0

            default_daily_hours = turn_rules.get("default_daily_hours", 12)

            if tipo_turno == 'NAO_TRABALHADO' or tipo_turno in ['FERIAS', 'LICENCA', 'BAIXA', 'FALTA_INJUSTIFICADA', 'FALTA_JUSTIFICADA', 'DISPENSA']:
                horas_normais = 0
                horas_extra = 0
                horas_fots = 0
            elif tipo_turno == 'FOLGA_OBRIGATORIA_SUPLEMENTAR':
                horas_fots = horas_trabalhadas
                horas_normais = 0
                horas_extra = 0
            elif tipo_turno in ['DIA_TRABALHO_SUPLEMENTAR', 'NOITE_TRABALHO_SUPLEMENTAR', 'DTS5S_ESPECIFICO', 'NTSS5S_ESPECIFICO', 'DTSDS_ESPECIFICO', 'NTSDS_ESPECIFICO']:
                horas_extra = horas_trabalhadas
                horas_normais = 0
                horas_fots = 0
            else: # Turnos de trabalho comuns (D, N, T, DT, NT, SA, SAT)
                if horas_trabalhadas <= default_daily_hours:
                    horas_normais = horas_trabalhadas
                    horas_extra = 0
                else:
                    horas_normais = default_daily_hours
                    horas_extra = horas_trabalhadas - default_daily_hours
            
            processed_data.append({
                'Nome': nome,
                'Funcao': funcao,
                'Data': current_date.strftime('%Y-%m-%d'),
                'Turno': turno_raw,
                'TipoTurno': tipo_turno,
                'HorasTrabalhadas': horas_trabalhadas,
                'HorasNormais': horas_normais,
                'HorasExtra': horas_extra,
                'HorasFOTS': horas_fots
            })
            
    return pd.DataFrame(processed_data)

# --- FUNÇÃO PARA SUMARIAR HORAS MENSAIS ---
def summarize_monthly_hours(daily_shifts_df):
    """
    Agrega o DataFrame de turnos diários para calcular os totais mensais
    de HorasTrabalhadas, HorasNormais, HorasExtra e HorasFOTS por colaborador.
    """
    if daily_shifts_df.empty:
        return pd.DataFrame()

    daily_shifts_df['Data'] = pd.to_datetime(daily_shifts_df['Data'])
    daily_shifts_df['Mes_Ano'] = daily_shifts_df['Data'].dt.to_period('M')

    monthly_summary_df = daily_shifts_df.groupby(['Nome', 'Funcao', 'Mes_Ano']).agg(
        TotalHorasTrabalhadas=('HorasTrabalhadas', 'sum'),
        TotalHorasNormais=('HorasNormais', 'sum'),
        TotalHorasExtra=('HorasExtra', 'sum'),
        TotalHorasFOTS=('HorasFOTS', 'sum')
    ).reset_index()

    monthly_summary_df['Mes_Ano'] = monthly_summary_df['Mes_Ano'].astype(str)

    monthly_summary_df = monthly_summary_df[[
        'Nome', 'Funcao', 'Mes_Ano', 
        'TotalHorasTrabalhadas', 'TotalHorasNormais', 
        'TotalHorasExtra', 'TotalHorasFOTS'
    ]]
    
    return monthly_summary_df

# --- FUNÇÃO PARA CALCULAR O ACERTO SEMESTRAL ---
def calculate_semester_settlement(monthly_summary_df_semester):
    """
    Calcula o acerto semestral de horas extra e FOTS com base nas regras fornecidas.

    Args:
        monthly_summary_df_semester (pd.DataFrame): DataFrame consolidado
                                                    com os resumos mensais por colaborador.

    Returns:
        pd.DataFrame: DataFrame com o resumo do acerto semestral por colaborador.
    """
    if monthly_summary_df_semester.empty:
        print("Aviso: DataFrame de resumo mensal consolidado está vazio. Não é possível calcular o acerto semestral.")
        return pd.DataFrame()

    # Agrupar por Nome e Função para somar as horas no semestre
    semester_settlement_df = monthly_summary_df_semester.groupby(['Nome', 'Funcao']).agg(
        TotalHorasExtraSemestre=('TotalHorasExtra', 'sum'),
        TotalHorasFOTSSemestre=('TotalHorasFOTS', 'sum')
    ).reset_index()

    # Regra: 12 horas = 1 dia de folga
    HOURS_PER_DAY_OFF = 12

    # 1. Tratar Horas Extra: Descontar negativas das positivas (já coberto pela soma)
    # A soma total já faz isto. Se um colaborador tiver +50h num mês e -20h noutro, o total será +30h.
    # Se o TotalHorasExtraSemestre for negativo, significa um défice de horas extra.

    # 2. Converter TotalHorasExtraSemestre em Dias de Folga Comp. (e saldo de horas)
    semester_settlement_df['DiasFolgaCompensatoria_HE'] = semester_settlement_df['TotalHorasExtraSemestre'] / HOURS_PER_DAY_OFF
    semester_settlement_df['SaldoHorasExtra_HE'] = semester_settlement_df['TotalHorasExtraSemestre'] % HOURS_PER_DAY_OFF
    
    # 3. Converter TotalHorasFOTSSemestre em Dias de Folga Comp. (e saldo de horas)
    semester_settlement_df['DiasFolgaCompensatoria_FOTS'] = semester_settlement_df['TotalHorasFOTSSemestre'] / HOURS_PER_DAY_OFF
    semester_settlement_df['SaldoHorasExtra_FOTS'] = semester_settlement_df['TotalHorasFOTSSemestre'] % HOURS_PER_DAY_OFF

    # Calcular o total de dias de folga compensatória
    semester_settlement_df['TotalDiasFolgaCompensatoria'] = \
        semester_settlement_df['DiasFolgaCompensatoria_HE'] + \
        semester_settlement_df['DiasFolgaCompensatoria_FOTS']
    
    # Calcular o saldo total de horas, que é a soma dos saldos de HE e FOTS
    # Pode haver um "carry-over" se, por exemplo, tiver 6h de HE e 6h de FOTS = 12h = 1 dia extra
    semester_settlement_df['SaldoHorasTotalAcerto'] = \
        semester_settlement_df['SaldoHorasExtra_HE'] + \
        semester_settlement_df['SaldoHorasExtra_FOTS']
    
    # Ajustar o SaldoHorasTotalAcerto e TotalDiasFolgaCompensatoria se o saldo total for >= 12h
    # Também tratar casos onde o saldo total é negativo (défice)
    
    # Horas acumuladas que podem ser convertidas em dias inteiros
    total_horas_acumuladas = semester_settlement_df['TotalHorasExtraSemestre'] + semester_settlement_df['TotalHorasFOTSSemestre']
    
    semester_settlement_df['TotalDiasFolgaCompensatoria'] = total_horas_acumuladas / HOURS_PER_DAY_OFF
    semester_settlement_df['SaldoHorasTotalAcerto'] = total_horas_acumuladas % HOURS_PER_DAY_OFF

    # Arredondar os dias de folga para duas casas decimais para clareza no relatório,
    # mas mantendo o cálculo de horas exato nos saldos.
    semester_settlement_df['DiasFolgaCompensatoria_HE'] = semester_settlement_df['DiasFolgaCompensatoria_HE'].round(2)
    semester_settlement_df['DiasFolgaCompensatoria_FOTS'] = semester_settlement_df['DiasFolgaCompensatoria_FOTS'].round(2)
    semester_settlement_df['TotalDiasFolgaCompensatoria'] = semester_settlement_df['TotalDiasFolgaCompensatoria'].round(2)


    # Reorganizar as colunas para o relatório
    semester_settlement_df = semester_settlement_df[[
        'Nome', 'Funcao',
        'TotalHorasExtraSemestre', 'DiasFolgaCompensatoria_HE', 'SaldoHorasExtra_HE',
        'TotalHorasFOTSSemestre', 'DiasFolgaCompensatoria_FOTS', 'SaldoHorasExtra_FOTS',
        'TotalDiasFolgaCompensatoria', 'SaldoHorasTotalAcerto'
    ]]

    return semester_settlement_df

# --- FUNÇÃO PARA GERAR RELATÓRIOS INDIVIDUAIS ---
def generate_individual_reports(daily_shifts_df, monthly_summary_df, output_dir, period_name):
    """
    Gera ficheiros Excel individuais para cada colaborador, contendo
    os seus turnos diários detalhados e o resumo mensal/período.

    Args:
        daily_shifts_df (pd.DataFrame): DataFrame com os turnos diários e cálculos de horas (consolidado).
        monthly_summary_df (pd.DataFrame): DataFrame com o resumo mensal/período por colaborador (consolidado).
        output_dir (str): Caminho para a pasta de saída.
        period_name (str): Nome do período (ex: "Semestre1_2025" ou "JAN_SVC2025").
    """
    if daily_shifts_df.empty or monthly_summary_df.empty:
        print("Aviso: Dados diários ou resumo mensal/período estão vazios. Não é possível gerar relatórios individuais.")
        return

    # Certifica-te de que a pasta 'individual_reports' existe
    individual_reports_dir = os.path.join(output_dir, 'Relatorios_Individuais')
    os.makedirs(individual_reports_dir, exist_ok=True)
    
    unique_names = daily_shifts_df['Nome'].unique()
    print(f"\nGerando relatórios individuais para {len(unique_names)} colaboradores para o período '{period_name}'...")

    for name in unique_names:
        # Filtrar dados diários para o colaborador atual
        collab_daily_df = daily_shifts_df[daily_shifts_df['Nome'] == name].copy()
        
        # Filtrar resumo mensal/período para o colaborador atual
        collab_monthly_df = monthly_summary_df[monthly_summary_df['Nome'] == name].copy()
        
        # Limpar o nome para usar no nome do ficheiro (remover caracteres especiais)
        safe_name = "".join(c for c in name if c.isalnum() or c.isspace()).strip()
        safe_name = safe_name.replace(" ", "_")

        output_file_name = f'Relatorio_{safe_name}_{period_name}.xlsx'
        output_file_path = os.path.join(individual_reports_dir, output_file_name)

        try:
            with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
                # Escrever a folha de detalhes diários
                collab_daily_df.to_excel(writer, sheet_name='Detalhe_Diario', index=False)
                
                # Ajustar a largura das colunas para o Detalhe_Diario
                for column in collab_daily_df:
                    column_length = max(collab_daily_df[column].astype(str).map(len).max(), len(column))
                    col_idx = collab_daily_df.columns.get_loc(column)
                    writer.sheets['Detalhe_Diario'].column_dimensions[chr(65 + col_idx)].width = column_length + 2

                # Escrever a folha de resumo mensal
                if not collab_monthly_df.empty:
                    collab_monthly_df.to_excel(writer, sheet_name='Resumo_Mensal_Periodo', index=False)
                    
                    # Ajustar a largura das colunas para o Resumo_Mensal
                    for column in collab_monthly_df:
                        column_length = max(collab_monthly_df[column].astype(str).map(len).max(), len(column))
                        col_idx = collab_monthly_df.columns.get_loc(column)
                        writer.sheets['Resumo_Mensal_Periodo'].column_dimensions[chr(65 + col_idx)].width = column_length + 2

            print(f"Relatório gerado para: {name} -> {output_file_path}")
        except Exception as e:
            print(f"Erro ao gerar relatório para {name}: {e}")

# --- BLOCO PRINCIPAL DE EXECUÇÃO (IF __NAME__ == "__MAIN__") ---
if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    
    excel_file_name = '01Jan_12Dez_Escala_Geral_2025_AHD.xlsx'
    input_file_path = os.path.join(project_root, 'data', 'input', excel_file_name)
    
    excel_year = 2025 # O ano para o qual os meses são lidos

    # Lista de meses/folhas a processar para o 1º semestre
    # Adicionar mais meses aqui à medida que os ficheiros ficam disponíveis
    list_of_months_to_process = [
        {'month_num': 1, 'sheet_name': 'JAN_SVC2025'},
        {'month_num': 2, 'sheet_name': 'FEV_SVC2025'},
        {'month_num': 3, 'sheet_name': 'MAR_SVC2025'},
        {'month_num': 4, 'sheet_name': 'ABR_SVC2025'},
        {'month_num': 5, 'sheet_name': 'MAI_SVC2025'},
        # {'month_num': 6, 'sheet_name': 'JUN_SVC2025'}, # Adicionar quando disponível
    ]

    config_file_path = os.path.join(project_root, 'config', 'turn_rules.json')
    rules = load_turn_rules(config_file_path)

    if rules is None:
        print("Não foi possível carregar as regras de turnos. Verifique o ficheiro config/turn_rules.json.")
        exit()

    # Listas para acumular os dados de todos os meses
    all_daily_shifts_dfs = []
    all_monthly_summary_dfs = []

    print(f"Iniciando processamento para o ano {excel_year} e meses definidos...")

    for month_info in list_of_months_to_process:
        month_num = month_info['month_num']
        sheet_name = month_info['sheet_name']
        
        print(f"\n--- Processando mês: {sheet_name} (Mês {month_num}) ---")
        
        scale_data_raw = read_scale_excel(input_file_path, sheet_name=sheet_name)

        if not scale_data_raw.empty:
            daily_shifts_df = process_scale_data(scale_data_raw, excel_year, month_num, rules)
            
            if not daily_shifts_df.empty:
                all_daily_shifts_dfs.append(daily_shifts_df)
                
                monthly_summary_df = summarize_monthly_hours(daily_shifts_df)
                if not monthly_summary_df.empty:
                    all_monthly_summary_dfs.append(monthly_summary_df)
                else:
                    print(f"Aviso: Resumo mensal vazio para a folha '{sheet_name}'.")
            else:
                print(f"Aviso: DataFrame de turnos diários vazio após processamento da folha '{sheet_name}'.")
        else:
            print(f"Aviso: DataFrame vazio após leitura da folha '{sheet_name}'.")

    # Concatenar todos os DataFrames acumulados
    if all_daily_shifts_dfs:
        daily_shifts_df_semester = pd.concat(all_daily_shifts_dfs, ignore_index=True)
        print(f"\n--- Dados diários consolidados para {len(all_daily_shifts_dfs)} meses ({daily_shifts_df_semester.shape[0]} linhas) ---")
    else:
        daily_shifts_df_semester = pd.DataFrame()
        print("\nErro: Nenhum dado diário foi processado com sucesso para o semestre.")

    if all_monthly_summary_dfs:
        monthly_summary_df_semester = pd.concat(all_monthly_summary_dfs, ignore_index=True)
        print(f"--- Resumo mensal consolidado para {len(all_monthly_summary_dfs)} meses ({monthly_summary_df_semester.shape[0]} linhas) ---")
    else:
        monthly_summary_df_semester = pd.DataFrame()
        print("Erro: Nenhum resumo mensal foi processado com sucesso para o semestre.")

    output_dir = os.path.join(project_root, 'data', 'output')
    os.makedirs(output_dir, exist_ok=True)

    # --- Exportar os DataFrames consolidados (para o semestre) ---
    if not daily_shifts_df_semester.empty:
        semester_period_name = f"JAN_MAI_{excel_year}" # Nome ajustado para o período atual
        output_excel_name_semester = f'Daily_Shifts_Calculated_Semestre_{semester_period_name}.xlsx'
        output_csv_name_semester = f'Daily_Shifts_Calculated_Semestre_{semester_period_name}.csv'
        
        daily_shifts_df_semester.to_excel(os.path.join(output_dir, output_excel_name_semester), index=False)
        print(f"\nDados diários consolidados exportados para Excel: {os.path.join(output_dir, output_excel_name_semester)}")
        daily_shifts_df_semester.to_csv(os.path.join(output_dir, output_csv_name_semester), index=False, encoding='utf-8')
        print(f"Dados diários consolidados exportados para CSV: {os.path.join(output_dir, output_csv_name_semester)}")
    
    if not monthly_summary_df_semester.empty:
        semester_period_name = f"JAN_MAI_{excel_year}"
        output_monthly_excel_name_semester = f'Monthly_Summary_Semestre_{semester_period_name}.xlsx'
        output_monthly_csv_name_semester = f'Monthly_Summary_Semestre_{semester_period_name}.csv'

        monthly_summary_df_semester.to_excel(os.path.join(output_dir, output_monthly_excel_name_semester), index=False)
        print(f"Resumo Mensal Consolidado exportado para Excel: {os.path.join(output_dir, output_monthly_excel_name_semester)}")
        monthly_summary_df_semester.to_csv(os.path.join(output_dir, output_monthly_csv_name_semester), index=False, encoding='utf-8')
        print(f"Resumo Mensal Consolidado exportado para CSV: {os.path.join(output_dir, output_monthly_csv_name_semester)}")
        
        # --- NOVO: Calcular e exportar o acerto semestral ---
        print("\n--- Calculando o Acerto Semestral de Horas ---")
        semester_settlement_final_df = calculate_semester_settlement(monthly_summary_df_semester)

        if not semester_settlement_final_df.empty:
            output_settlement_excel_name = f'Acerto_Semestral_JAN_MAI_{excel_year}.xlsx'
            output_settlement_csv_name = f'Acerto_Semestral_JAN_MAI_{excel_year}.csv'
            
            semester_settlement_final_df.to_excel(os.path.join(output_dir, output_settlement_excel_name), index=False)
            print(f"Acerto Semestral exportado para Excel: {os.path.join(output_dir, output_settlement_excel_name)}")
            semester_settlement_final_df.to_csv(os.path.join(output_dir, output_settlement_csv_name), index=False, encoding='utf-8')
            print(f"Acerto Semestral exportado para CSV: {os.path.join(output_dir, output_settlement_csv_name)}")
        else:
            print("Aviso: O DataFrame do acerto semestral está vazio. Nenhum relatório de acerto foi gerado.")

        # --- Gerar Relatórios Individuais por Colaborador para o período consolidado ---
        print("\n--- Iniciando a geração de relatórios individuais consolidados... ---")
        generate_individual_reports(daily_shifts_df_semester, monthly_summary_df_semester, output_dir, semester_period_name)
        print("\n--- Geração de relatórios individuais consolidados concluída. ---")

    else:
        print("\nNão foi possível gerar dados consolidados ou resumos mensais para o semestre.")
