import streamlit as st
import pandas as pd
import os
import sys

# --- Correção para garantir que o módulo excel_reader é encontrado ---
# Adiciona o diretório raiz do projeto ao sys.path.
# Isto permite importar módulos de subpastas como 'src.excel_reader'.
script_dir = os.path.dirname(__file__)
# project_root agora aponta para C:\Users\subrg\Documents\Projetos\teste_projeto_david_sardinha
project_root = os.path.abspath(os.path.join(script_dir))
sys.path.insert(0, project_root) # Adiciona a raiz do projeto ao PATH

# Importar as funções de processamento de dados do excel_reader
# Agora importamos como 'src.excel_reader' para usar o novo PATH
try:
    from src.excel_reader import read_scale_excel, process_scale_data, summarize_monthly_hours, calculate_semester_settlement, generate_individual_reports, load_turn_rules
except ModuleNotFoundError as e:
    st.error(f"Erro Crítico: Não foi possível carregar o módulo 'excel_reader'.")
    st.error(f"Por favor, verifique se 'excel_reader.py' está localizado na pasta 'src' dentro da pasta principal do projeto.")
    st.error(f"Detalhes do erro: {e}")
    st.stop() # Para a execução do Streamlit se o módulo não for encontrado

# --- Configurações e Caminhos (devem ser os mesmos que em excel_reader.py) ---
# Usa project_root para construir os caminhos relativos ao projeto
data_output_dir = os.path.join(project_root, 'data', 'output')
individual_reports_dir = os.path.join(data_output_dir, 'Relatorios_Individuais')

# Nomes dos ficheiros gerados pelo excel_reader.py
DAILY_SHIFTS_FILE = 'Daily_Shifts_Calculated_Semestre_JAN_MAI_2025.xlsx'
MONTHLY_SUMMARY_FILE = 'Monthly_Summary_Semestre_JAN_MAI_2025.xlsx'
SEMESTER_SETTLEMENT_FILE = 'Acerto_Semestral_JAN_MAI_2025.xlsx'

# --- Funções para Carregar Dados Processados ---
@st.cache_data # Decorador para cachear os dados e evitar recarregar a cada interação
def load_processed_data():
    """Carrega os DataFrames processados do disco."""
    daily_df = pd.DataFrame()
    monthly_df = pd.DataFrame()
    settlement_df = pd.DataFrame()

    try:
        daily_df = pd.read_excel(os.path.join(data_output_dir, DAILY_SHIFTS_FILE))
        # Converter a coluna 'Data' para datetime para facilitar filtros e ordenação
        daily_df['Data'] = pd.to_datetime(daily_df['Data'])
    except FileNotFoundError:
        st.error(f"Ficheiro de turnos diários '{DAILY_SHIFTS_FILE}' não encontrado.")
        st.info("Por favor, execute 'python src\\excel_reader.py' no terminal para gerar os dados primeiro.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame() # Retorna DataFrames vazios para evitar erros posteriores
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro de turnos diários: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        monthly_df = pd.read_excel(os.path.join(data_output_dir, MONTHLY_SUMMARY_FILE))
    except FileNotFoundError:
        st.error(f"Ficheiro de resumo mensal '{MONTHLY_SUMMARY_FILE}' não encontrado.")
        st.info("Por favor, execute 'python src\\excel_reader.py' no terminal para gerar os dados primeiro.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro de resumo mensal: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    try:
        settlement_df = pd.read_excel(os.path.join(data_output_dir, SEMESTER_SETTLEMENT_FILE))
    except FileNotFoundError:
        st.error(f"Ficheiro de acerto semestral '{SEMESTER_SETTLEMENT_FILE}' não encontrado.")
        st.info("Por favor, execute 'python src\\excel_reader.py' no terminal para gerar os dados primeiro.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar ficheiro de acerto semestral: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    return daily_df, monthly_df, settlement_df

# --- Layout da Aplicação Streamlit ---
st.set_page_config(layout="wide", page_title="Gestão de Horas de Trabalho")

st.title("Sistema de Gestão de Horas de Trabalho")
st.subheader("Relatórios Semestrais e Acerto de Horas")

# Carregar os dados
daily_shifts_df, monthly_summary_df, semester_settlement_df = load_processed_data()

# Verificar se os DataFrames estão vazios e exibir mensagens de erro
if daily_shifts_df.empty or monthly_summary_df.empty or semester_settlement_df.empty:
    st.warning("Um ou mais DataFrames de dados não foram carregados. A aplicação pode não exibir todos os dados.")
    st.stop() # Parar a execução da aplicação Streamlit se os dados não existirem.

# --- Abas para organizar o conteúdo ---
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard Geral", "Consulta Individual", "Acerto Semestral", "Recarregar Dados"])

with tab1:
    st.header("Dashboard Geral - Semestre (JAN-MAI 2025)")

    # Métricas gerais
    if not monthly_summary_df.empty:
        total_horas_normais_geral = monthly_summary_df['TotalHorasNormais'].sum()
        total_horas_extra_geral = monthly_summary_df['TotalHorasExtra'].sum()
        total_horas_fots_geral = monthly_summary_df['TotalHorasFOTS'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Horas Normais (Semestre)", f"{total_horas_normais_geral:.2f}h")
        with col2:
            st.metric("Total Horas Extra (Semestre)", f"{total_horas_extra_geral:.2f}h")
        with col3:
            st.metric("Total Horas FOTS (Semestre)", f"{total_horas_fots_geral:.2f}h")

        st.markdown("---")

        st.subheader("Resumo Mensal Consolidado (Geral)")
        # Agrupar por Mês_Ano e somar para ter um resumo por mês para todo o pessoal
        monthly_summary_per_month = monthly_summary_df.groupby('Mes_Ano').agg(
            TotalHorasTrabalhadas=('TotalHorasTrabalhadas', 'sum'),
            TotalHorasNormais=('TotalHorasNormais', 'sum'),
            TotalHorasExtra=('TotalHorasExtra', 'sum'),
            TotalHorasFOTS=('TotalHorasFOTS', 'sum')
        ).reset_index()
        st.dataframe(monthly_summary_per_month.sort_values('Mes_Ano'), use_container_width=True)

        st.subheader("Top 5 Colaboradores com Mais Horas Extra")
        top_extra = monthly_summary_df.groupby('Nome')['TotalHorasExtra'].sum().nlargest(5)
        st.bar_chart(top_extra)

        st.subheader("Top 5 Colaboradores com Mais Horas FOTS")
        top_fots = monthly_summary_df.groupby('Nome')['TotalHorasFOTS'].sum().nlargest(5)
        st.bar_chart(top_fots)

        st.subheader("Distribuição por Função")
        func_summary = monthly_summary_df.groupby('Funcao').agg(
            TotalHorasNormais=('TotalHorasNormais', 'sum'),
            TotalHorasExtra=('TotalHorasExtra', 'sum')
        ).reset_index().sort_values('TotalHorasNormais', ascending=False)
        st.dataframe(func_summary, use_container_width=True)


with tab2:
    st.header("Consulta Individual de Colaboradores")

    # Obter lista de nomes únicos para a caixa de seleção
    if not daily_shifts_df.empty:
        colaboradores = daily_shifts_df['Nome'].unique()
        colaboradores_sorted = sorted(colaboradores) # Ordenar alfabeticamente

        selected_colaborador = st.selectbox("Selecione um Colaborador:", colaboradores_sorted)

        if selected_colaborador:
            st.subheader(f"Dados para {selected_colaborador}")

            # Filtrar resumo mensal/período para o colaborador
            collab_monthly_df = monthly_summary_df[monthly_summary_df['Nome'] == selected_colaborador].copy()
            if not collab_monthly_df.empty:
                st.write("### Resumo Mensal/Período")
                st.dataframe(collab_monthly_df.set_index('Mes_Ano'), use_container_width=True)
            else:
                st.info("Nenhum resumo mensal encontrado para este colaborador no período selecionado.")

            # Filtrar dados diários para o colaborador
            collab_daily_df = daily_shifts_df[daily_shifts_df['Nome'] == selected_colaborador].copy()
            if not collab_daily_df.empty:
                st.write("### Detalhes Diários")
                # Exibir as colunas relevantes para o detalhe diário
                st.dataframe(collab_daily_df[['Data', 'Turno', 'TipoTurno', 'HorasTrabalhadas', 'HorasNormais', 'HorasExtra', 'HorasFOTS']], use_container_width=True)
            else:
                st.info("Nenhum detalhe diário encontrado para este colaborador no período selecionado.")

            # Link para o relatório individual
            st.write("### Relatório Individual (Excel)")
            # Trata nomes com carateres especiais ou espaços para o nome do ficheiro
            safe_name = "".join(c for c in selected_colaborador if c.isalnum() or c.isspace()).strip()
            safe_name = safe_name.replace(" ", "_")
            report_filename = f'Relatorio_{safe_name}_JAN_MAI_2025.xlsx'
            report_path = os.path.join(individual_reports_dir, report_filename)

            if os.path.exists(report_path):
                with open(report_path, "rb") as file:
                    st.download_button(
                        label=f"Descarregar Relatório de {selected_colaborador}",
                        data=file,
                        file_name=report_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning(f"O relatório individual para {selected_colaborador} não foi encontrado. Por favor, execute 'python src\\excel_reader.py' para gerá-lo.")
    else:
        st.info("Nenhum colaborador encontrado nos dados diários. Por favor, verifique se os dados foram processados.")

with tab3:
    st.header("Acerto Semestral de Horas (JAN-MAI 2025)")
    st.write("Esta tabela mostra o cálculo do acerto de horas extra e FOTS para o período semestral, resultando em dias de folga compensatória e saldo de horas.")
    if not semester_settlement_df.empty:
        st.dataframe(semester_settlement_df, use_container_width=True)
    else:
        st.info("O DataFrame do acerto semestral está vazio. Por favor, verifique se os dados foram processados.")

with tab4:
    st.header("Recarregar Dados")
    st.write("Utilize esta opção para recarregar os dados se tiver atualizado os ficheiros Excel de entrada ou o script de processamento.")
    if st.button("Recarregar Dados (Limpar Cache)"):
        load_processed_data.clear() # Limpa a cache da função de carregamento de dados
        st.rerun() # Reinicia todo o script
        st.success("Dados recarregados com sucesso!")