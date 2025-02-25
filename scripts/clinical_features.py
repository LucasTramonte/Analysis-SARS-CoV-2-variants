# Exploratory Clinical Features

# Libraries
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Datasets
df_original = pd.read_csv('Assets/Data/df_preprocessed.csv', delimiter=',')

df = df_original.copy(deep=True)
df.drop(columns=['Unnamed: 0'], inplace=True)

# CONSTANTS
DICT_PADRAO = {1: 'Yes', 2: 'Not', 9: 'Ignored'}
FAIXA_PADRAO = ['Yes', 'Not']
VARIANT_NAMES = {1: 'Gamma', 2: 'Delta', 3: 'Omicron'}

# Mapping dictionaries
Clinical_features = {
    'FEBRE': 'Fever',
    'TOSSE': 'Cough',
    'GARGANTA': 'Sore Throat',
    'DISPNEIA': 'Dyspnea',
    'DESC_RESP': 'Respiratory Discomfort',
    'SATURACAO': 'Oxygen Saturation',
    'DIARREIA': 'Diarrhea',
    'VOMITO': 'Vomiting',
    'DOR_ABD': 'Abdominal Pain',
    'FADIGA': 'Fatigue',
    'PERD_OLFT': 'Loss of Smell',
    'PERD_PALA': 'Loss of Taste'
}

for column in Clinical_features.keys():
    df[column] = df[column].map(DICT_PADRAO)

# Rename columns to English
df.rename(columns=Clinical_features, inplace=True)

def calculate_chi_square(plot_df: pd.DataFrame) -> float:
    """
    Calculate the chi-square statistic for the given DataFrame.
    """
    chi_square = 0
    columns = plot_df.columns[:-1]  # Exclude 'Total' column
    rows = plot_df.index[:-1]  # Exclude 'Total' row

    for variant in columns:
        for category in rows:
            observed = plot_df.at[category, variant]
            expected = plot_df.at[category, 'Total'] * plot_df.at['Total', variant] / plot_df.at['Total', 'Total']
            chi_square += (observed - expected) ** 2 / expected

    return chi_square

def save_plot(plot_df: pd.DataFrame, variable: str) -> None:
    """
    Save a bar plot of the distribution of COVID-19 variants by the given variable.
    """
    ax = plot_df.plot(kind='bar', figsize=(10, 6))
    plt.title(f'Distribution of COVID-19 Variants by {variable}')
    plt.xlabel(variable)
    plt.ylabel('Number of Samples')
    plt.legend(title='COVID Variant', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
    plt.tight_layout()
    output_dir = Path(f'Assets/Output/Clinical features/{variable}')
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / f'{variable}_distribution.png')
    plt.close()

def save_results(output_dir: Path, variable: str, p_value: float, conclusion: str) -> None:
    """
    Save the results of the chi-square test to a text file.
    """
    with open(output_dir / f'{variable}_results.txt', 'w', encoding='utf-8') as f:
        f.write(f'H₀: The two categorical variables ({variable} and VARIANTE_COVID) have no relationship\n')
        f.write(f'p-value: {p_value}\n')
        f.write(conclusion)

def plot_and_test_relationship(df: pd.DataFrame, label: list, variable: str, alpha: float = 0.05) -> None:
    """
    Plot the distribution of COVID-19 variants by the given variable and perform a chi-square test.
    """
    plot_df = pd.DataFrame(index=label)

    for variant in df['VARIANTE_COVID'].unique():
        variant_counts = df[df['VARIANTE_COVID'] == variant].loc[df[variable] != 'Ignored'].groupby(variable).size()
        plot_df[VARIANT_NAMES[variant]] = variant_counts

    plot_df['Total'] = plot_df.sum(axis=1)
    plot_df.loc['Total'] = plot_df.sum()

    percentage_df = plot_df.copy()
    for variant in VARIANT_NAMES.values():
        percentage_df[f'{variant}_Percentage'] = (percentage_df[variant] / percentage_df.at['Total', variant] * 100).round(2).astype(str) + '%'

    column_order = [f'{variant}' for variant in VARIANT_NAMES.values()] + [f'{variant}_Percentage' for variant in VARIANT_NAMES.values()] + ['Total']
    percentage_df = percentage_df[column_order]

    output_dir = Path(f'Assets/Output/Clinical features/{variable}')
    output_dir.mkdir(parents=True, exist_ok=True)
    percentage_df.to_csv(output_dir / f'{variable}_percentages.csv')

    chi_square = calculate_chi_square(plot_df)
    p_value = 1 - stats.chi2.cdf(chi_square, (len(plot_df.index) - 1) * (len(plot_df.columns) - 1))

    conclusion = "Failed to reject the null hypothesis."
    if p_value <= alpha:
        conclusion = "Null Hypothesis is rejected."

    save_plot(plot_df, variable)
    save_results(output_dir, variable, p_value, conclusion)

for feature in Clinical_features.values():
    plot_and_test_relationship(df, FAIXA_PADRAO, feature)