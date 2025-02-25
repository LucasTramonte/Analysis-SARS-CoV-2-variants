import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import os

# Constants
DATA_PATH = os.path.join('..', 'Assets', 'Data', 'df_preprocessed.csv')
OUTPUT_DIR = os.path.join('..', 'Assets', 'Output', 'Sociodemographic Obstetrical features')
AGE_GROUPS = ['0-19', '20-24', '25-29', '30-34', '35-39', '40+']
ETHNICITY_GROUPS = ['White', 'Black', 'Others']
ETHNICITY_DICT = {1: 'White', 2: 'Black', 3: 'Others', 4: 'Others', 5: 'Others', 9: 'Ignored'}
EDUCATION_LEVELS = ['None or Primary incomplete', 'Primary', 'Secondary', 'College or more']
EDUCATION_DICT = {0: 'None or Primary incomplete', 1: 'None or Primary incomplete', 2: 'Primary', 3: 'Secondary', 4: 'College or more', 5: 'Ignored', 9: 'Ignored'}
PREGNANCY_STAGES = ['First trimester', 'Second trimester', 'Third trimester', 'Gestation period ignored', 'Puerpera']
PREGNANCY_DICT = {1: 'First trimester', 2: 'Second trimester', 3: 'Third trimester', 4: 'Gestation period ignored', 5: 'Puerpera'}
VACCINATION_DICT = {1: 'at least 1 dose', 2: 'Unvaccinated', 9: 'Ignored'}
VACCINATION_GROUPS = ['at least 1 dose', 'Unvaccinated']
REGION_GROUPS = ['North', 'Northeast', 'Southeast', 'South', 'Midwest']
REGION_DICT = {1: 'North', 2: 'Northeast', 3: 'Southeast', 4: 'South', 5: 'Midwest'}
STANDARD_DICT = {1: 'Yes', 2: 'Not', 9: 'Ignored'}
STANDARD_GROUPS = ['Yes', 'Not']
VARIANT_NAMES = {1: 'Gamma', 2: 'Delta', 3: 'Omicron'}

# Load dataset
try:
    df_original = pd.read_csv(DATA_PATH, delimiter=',')
except FileNotFoundError:
    print(f"Error: The file at {DATA_PATH} was not found.")
    exit(1)

# Preprocess dataset
df = df_original.copy(deep=True)
df.drop(columns=['Unnamed: 0'], inplace=True)

# Mapping dictionaries
df['Ethnicity'] = df['CS_RACA'].map(ETHNICITY_DICT)
df['Education_Level'] = df['CS_ESCOL_N'].map(EDUCATION_DICT)
df['Pregnancy'] = df['GRAVIDEZ'].map(PREGNANCY_DICT)
df['COVID_Vaccination'] = df['VACINA_COV'].map(VACCINATION_DICT)
df['Chronic_Cardiovascular_Disease'] = df['CARDIOPATI'].map(STANDARD_DICT)
df['Kidney_Disease'] = df['RENAL'].map(STANDARD_DICT)
df['Asthma'] = df['ASMA'].map(STANDARD_DICT)
df['Diabetes'] = df['DIABETES'].map(STANDARD_DICT)
df['Brazil_Region'] = df['Regiao'].map(REGION_DICT)

other_diseases = {
    'Chronic_Hematological_Disease': 'HEMATOLOGI',
    'Down_Syndrome': 'SIND_DOWN',
    'Chronic_Liver_Disease': 'HEPATICA',
    'Neurological_Disease': 'NEUROLOGIC',
    'Pneumopathy': 'PNEUMOPATI',
    'Immunodeficiency_or_Immunodepression': 'IMUNODEPRE',
    'Obesity': 'OBESIDADE'
}

for new_col, old_col in other_diseases.items():
    df[new_col] = df[old_col].map(STANDARD_DICT)

# Create age groups
bins = [0, 19, 24, 29, 34, 39, float('inf')]
df['Age'] = pd.cut(df['NU_IDADE_N'], bins=bins, labels=AGE_GROUPS, right=True)

def plot_and_test_relationship(df, label, variable, output_dir, alpha=0.05):
    """
    Plots the distribution of COVID-19 variants by a given variable and performs a chi-square test.

    Parameters:
    df (pd.DataFrame): The dataframe containing the data.
    label (list): The labels for the variable.
    variable (str): The variable to analyze.
    output_dir (str): The directory to save the output files.
    alpha (float): The significance level for the chi-square test.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    plot_df = pd.DataFrame(index=label)
    for variant in df['VARIANTE_COVID'].unique():
        variant_counts = df[df['VARIANTE_COVID'] == variant].loc[df[variable] != 'Ignored'].groupby(variable).size()
        plot_df[variant] = variant_counts

    plot_df.rename(columns=VARIANT_NAMES, inplace=True)

    ax = plot_df.plot(kind='bar', figsize=(10, 6))
    plt.title(f'Distribution of COVID-19 Variants by {variable}')
    plt.xlabel(variable)
    plt.ylabel('Number of Samples')
    plt.legend(title='COVID Variant', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
    plt.savefig(os.path.join(output_dir, 'plot.png'), bbox_inches='tight')
    plt.close()

    plot_df['Total'] = plot_df.sum(axis=1)
    plot_df.loc['Total'] = plot_df.sum()

    percentage_df = plot_df.copy()
    for variant in VARIANT_NAMES.values():
        percentage_df[variant + '_Percentage'] = (percentage_df[variant] / percentage_df.loc['Total'][variant] * 100).round(2).astype(str) + '%'

    column_order = [variant for variant in VARIANT_NAMES.values()] + [variant + '_Percentage' for variant in VARIANT_NAMES.values()] + ['Total']
    percentage_df = percentage_df[column_order]
    percentage_df.to_csv(os.path.join(output_dir, 'percentage.csv'))

    chi2, p_value, _, _ = stats.chi2_contingency(plot_df.iloc[:-1, :-1])
    with open(os.path.join(output_dir, 'p_value.txt'), 'w', encoding='utf-8') as f:
        f.write(f'H₀: The two categorical variables ({variable} and VARIANTE_COVID) have no relationship\n')
        f.write(f'p-value: {p_value}\n')
        conclusion = "Failed to reject the null hypothesis."
        if p_value <= alpha:
            conclusion = "Null Hypothesis is rejected."
        f.write(conclusion)

def analyze_relationships(df, relationships, output_dir):
    """
    Analyzes the relationships between COVID-19 variants and various sociodemographic and obstetrical features.

    Parameters:
    df (pd.DataFrame): The dataframe containing the data.
    relationships (dict): A dictionary of variables and their labels to analyze.
    output_dir (str): The directory to save the output files.
    """
    for variable, label in relationships.items():
        plot_and_test_relationship(df, label, variable, os.path.join(output_dir, variable.replace("_", " ")))

# Define relationships
relationships = {
    'Ethnicity': ETHNICITY_GROUPS,
    'Education_Level': EDUCATION_LEVELS,
    'Pregnancy': PREGNANCY_STAGES,
    'COVID_Vaccination': VACCINATION_GROUPS,
    'Brazil_Region': REGION_GROUPS,
    'Chronic_Cardiovascular_Disease': STANDARD_GROUPS,
    'Kidney_Disease': STANDARD_GROUPS,
    'Asthma': STANDARD_GROUPS,
    'Diabetes': STANDARD_GROUPS,
    'Age': AGE_GROUPS, 
    'Chronic_Hematological_Disease': STANDARD_GROUPS  
}

# Combine predefined relationships and other diseases
all_relationships = {**relationships, **{k: STANDARD_GROUPS for k in other_diseases.keys()}}

# Analyze all relationships
analyze_relationships(df, all_relationships, OUTPUT_DIR)