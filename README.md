# Sistema Automatizado de Gestão e Acerto de Horas de Trabalho

## Visão Geral do Projeto
Este projeto envolveu o desenvolvimento de um sistema completo para a automatização da gestão e contabilização detalhada das horas de trabalho de colaboradores, com foco na otimização de processos manuais e na provisão de dados para o acerto semestral de horas. A solução inclui um motor de cálculo robusto em Python e uma interface web interativa para visualização e análise dos dados.

## O Problema / O Desafio
O cliente enfrentava um desafio significativo na gestão de horas de trabalho, que se baseava em processos manuais e demorados a partir de complexas escalas de trabalho em Excel. Esta abordagem era altamente suscetível a erros, dificultava a monitorização em tempo real do desempenho de horas e tornava o acerto semestral de horas extra e horas em Folgas Obrigatórias (FOTS) um processo complexo e ineficiente. A falta de uma visão consolidada impedia decisões rápidas e baseadas em dados.

## A Solução Implementada
Desenvolvi uma solução automatizada em Python que transforma eficientemente os dados das escalas Excel em informações acionáveis. O sistema:
1.  **Processa dados de escala:** Importa e interpreta as escalas de trabalho diárias.
2.  **Contabiliza horas:** Calcula com precisão horas normais, horas extra e horas FOTS para cada colaborador, com base em regras de turnos personalizáveis.
3.  **Automatiza o Acerto Semestral:** Agrega dados mensais para calcular o acerto semestral de horas, determinando o saldo de horas extra e a necessidade de dias de folga compensatória.
4.  **Gera Relatórios Detalhados:** Produz relatórios diários, mensais, semestrais e individuais em formato Excel/CSV.
5.  **Oferece Visualização Interativa:** Uma aplicação web construída com Streamlit permite aos gestores visualizar dashboards consolidados, consultar dados individuais de colaboradores e descarregar relatórios diretamente do navegador.
Aqui está uma visão geral do dashboard principal da aplicação, mostrando os totais consolidados de horas para o semestre e um resumo mensal.
![Dashboard Geral da Aplicação Streamlit com resumos de horas por semestre e mês](https://github.com/user-attachments/assets/c91d0d74-a267-4f3b-9b35-3e3c2c0d0649)

## Tecnologias Utilizadas
* **Linguagem de Programação:** Python
* **Análise e Manipulação de Dados:** Pandas
* **Leitura/Escrita de Excel:** OpenPyXL
* **Desenvolvimento Web/UI:** Streamlit
* **Gestão de Ambientes/Dependências:** `venv` (ambiente virtual Python)

## Funcionalidades Chave
* **Processamento de Escalas Excel:** Leitura automatizada e transformação de dados de escalas complexas.
* **Cálculo Preciso de Horas:** Contabilização de Horas Normais, Horas Extra e Horas em Folgas Obrigatórias (FOTS) por colaborador e por turno.
* **Acerto Semestral Automatizado:** Cálculo de saldos de horas e determinação de dias de folga compensatória.
* Uma funcionalidade crucial do sistema é o acerto semestral automatizado, que calcula os saldos de horas e as folgas compensatórias necessárias.
![Secção de Acerto Semestral da Aplicação Streamlit com cálculo de saldos de horas]((https://github.com/user-attachments/assets/7ffb7aa3-e890-4e87-9961-f69b556c4bbe)
* **Geração de Relatórios:** Exportação de dados para Excel/CSV (detalhes diários, resumos mensais, acerto semestral, relatórios individuais).

A interface intuitiva permite a consulta de detalhes de horas por colaborador, com acesso a resumos diários e mensais.
* **Dashboard Interativo:** Visualização consolidada de métricas gerais do semestre (Total de Horas Normais, Extra, FOTS).
* **Consulta Individual de Colaboradores:** Filtro por nome para ver detalhes diários e resumos mensais de cada colaborador.
* A interface intuitiva permite a consulta de detalhes de horas por colaborador, com acesso a resumos diários e mensais.
  ![Interface de Consulta Individual de Colaborador com detalhes diários e mensais](https://github.com/user-attachments/assets/8cf2fa74-3de1-4ff6-aa0d-38b4c498a44d)

* **Download de Relatórios Individuais:** Capacidade de descarregar relatórios Excel específicos para cada colaborador diretamente da aplicação web.
* **Configuração Flexível:** Regras de turnos e horas definidas num ficheiro JSON (`turn_rules.json`) para fácil atualização.

Uma funcionalidade crucial do sistema é o acerto semestral automatizado, que calcula os saldos de horas e as folgas compensatórias necessárias.
## Resultados e Impacto
A implementação deste sistema resultou numa melhoria significativa da eficiência operacional do cliente. Conseguiu-se:
* Redução drástica do tempo gasto na contabilização e acerto de horas.
* Eliminação de erros humanos no processo manual.
* Acesso a uma visão clara e instantânea do desempenho de horas da equipa.
* Simplificação de um processo complexo (acerto semestral), garantindo conformidade e transparência na gestão de recursos humanos.
* O processamento de dados subjacente, gerido pelo script Python, garante a extração e transformação eficiente das escalas de trabalho.
![Processamento de Dados de Escala na Linha de Comandos (Back-end)](https://github.com/user-attachments/assets/b217fb0b-a132-4d74-a94e-5ef93a30a55b)



O processamento de dados subjacente, gerido pelo script Python, garante a extração e transformação eficiente das escalas de trabalho.
---

**NOTA SOBRE DADOS:** Por razões de confidencialidade e privacidade do cliente, todos os dados exibidos nas screenshots e em qualquer demonstração são fictícios e foram gerados apenas para fins de portefólio.
