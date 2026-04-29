# /// script

# dependencies = [

#     "marimo",

#     "pandas==3.0.2",

#     "plotly==6.7.0",

# ]

# requires-python = ">=3.13"

# ///

 

import marimo
import micropip

await micropip.install(["plotly", "pandas"])   
 

__generated_with = "0.23.4"

app = marimo.App(width="full")

 

 

@app.cell

def _():

    import marimo as mo

    import pandas as pd

    import plotly.express as px

    import plotly.graph_objects as go

 

    return go, mo, pd, px

 

 

@app.cell

def _(mo):

    mo.md("""

    # Ekonomisk Simulator 2025–2035

 

    Simulera effekten av tomträttsavgäldsförändringen 2030 och andra ekonomiska beslut.

 

    **Bakgrund:** Tomträttsavgäldsperioden löper t.o.m. 2030-04-30 och omförhandlas därefter.

    Vid omförhandling tillämpas vanligen en 5-årig upptrappning ("stege") till den nya nivån.

    """)

    return

 

 

@app.cell

def _(mo):

    # Sliders

    fee_change_slider = mo.ui.slider(

        start=0, stop=15, step=0.5, value=5,

        label="Årsavgift bostäder — årlig höjning (%)"

    )

    commercial_change_slider = mo.ui.slider(

        start=0, stop=10, step=0.5, value=2,

        label="Hyresintäkter lokaler — årlig höjning (%)"

    )

    tomtratt_slider = mo.ui.slider(

        start=80, stop=130, step=5, value=100,

        label="Tomträttsavgäld ökning 2030 (%)"

    )

    amortization_slider = mo.ui.slider(

        start=0, stop=1_000_000, step=50_000, value=500_000,

        label="Amortering per år (kr)"

    )

    amort_change_slider = mo.ui.slider(

        start=-10, stop=10, step=1, value=0,

        label="Amortering — årlig förändring (%)"

    )

    interest_rate_slider = mo.ui.slider(

        start=1.0, stop=6.0, step=0.1, value=2.5,

        label="Snittränta på lån (%)"

    )

    other_costs_slider = mo.ui.slider(

        start=0, stop=8, step=0.5, value=2,

        label="Övriga kostnader — årlig ökning (%)"

    )

    amort_excess_checkbox = mo.ui.checkbox(

        value=False,

        label="Amortera överskott (fritt kassaflöde)"

    )

 

    controls = mo.vstack([

        mo.md("## Inställningar"),

        mo.hstack([fee_change_slider, commercial_change_slider], justify="start"),

        mo.hstack([tomtratt_slider, interest_rate_slider], justify="start"),

        mo.hstack([amortization_slider, amort_change_slider], justify="start"),

        mo.hstack([other_costs_slider, amort_excess_checkbox], justify="start"),

    ])

    controls

    return (

        amort_change_slider,

        amort_excess_checkbox,

        amortization_slider,

        commercial_change_slider,

        fee_change_slider,

        interest_rate_slider,

        other_costs_slider,

        tomtratt_slider,

    )

 

 

@app.cell(hide_code=True)

def _(

    amort_change_slider,

    amort_excess_checkbox,

    amortization_slider,

    commercial_change_slider,

    fee_change_slider,

    go,

    interest_rate_slider,

    mo,

    other_costs_slider,

    pd,

    px,

    tomtratt_slider,

):

    # === Base data from 2025 annual report ===

    TOTAL_AREA = 1_359  # m² total

    BOSTADSYTA = 1_151  # m² bostadsrätt

 

    # 2025 values

    base_year = 2025

    base_arsavgift_bostader = 893_472

    base_hyra_lokaler = 729_216

    base_fastighetsskatt_vidare = 80_609

    base_tomtratt = 358_200

    base_drift_exkl_tomtratt = 1_095_142 - 358_200  # drift minus tomträtt

    base_ovriga_ext = 86_212

    base_avskrivningar = 368_302

    base_skuld = 7_500_000

    base_amort = 500_000

 

    # Apartment sizes

    apartments = [

        {"typ": "1 rok", "antal": 4, "snitt_yta": 25.0},

        {"typ": "2 rok", "antal": 9, "snitt_yta": 57.4},

        {"typ": "3 rok", "antal": 2, "snitt_yta": 107.0},

        {"typ": "4 rok", "antal": 3, "snitt_yta": 106.7},

    ]

 

    # Slider values

    fee_pct = fee_change_slider.value / 100

    commercial_pct = commercial_change_slider.value / 100

    tomtratt_increase_pct = tomtratt_slider.value / 100

    amort_yearly = amortization_slider.value

    amort_change_pct = amort_change_slider.value / 100

    interest_rate = interest_rate_slider.value / 100

    other_costs_pct = other_costs_slider.value / 100

    amort_excess = amort_excess_checkbox.value

 

    # === Simulation ===

    years = list(range(2025, 2036))

    rows = []

    running_debt = base_skuld

 

    for i, year in enumerate(years):

        # --- Income ---

        arsavgift = base_arsavgift_bostader * (1 + fee_pct) ** i

        hyra_lokaler = base_hyra_lokaler * (1 + commercial_pct) ** i

        fastighetsskatt = base_fastighetsskatt_vidare  # roughly constant

 

        # --- Tomträttsavgäld with 5-year ladder from 2031 ---

        new_tomtratt = base_tomtratt * (1 + tomtratt_increase_pct)

        if year <= 2030:

            tomtratt = base_tomtratt

        else:

            # 5-year ladder: each year adds 1/5 of the difference

            step = min(year - 2030, 5)

            tomtratt = base_tomtratt + (new_tomtratt - base_tomtratt) * (step / 5)

 

        # --- Debt & interest ---

        ranta = running_debt * interest_rate

 

        # --- Other costs (grow ~2%/year) ---

        drift_ovrig = base_drift_exkl_tomtratt * ((1 + other_costs_pct) ** i)

        ovriga_ext = base_ovriga_ext * ((1 + other_costs_pct) ** i)

        avskrivningar = base_avskrivningar  # constant

 

        # --- Totals ---

        total_intakter = arsavgift + hyra_lokaler + fastighetsskatt

        total_kostnader = tomtratt + drift_ovrig + ovriga_ext + avskrivningar + ranta

 

        # --- Amortization ---

        if amort_excess:

            # Amortize the free cashflow (income - costs excl. amortization)

            amort_this_year = max(0, total_intakter - total_kostnader)

        else:

            amort_this_year = amort_yearly * (1 + amort_change_pct) ** i

        amort_this_year = min(amort_this_year, running_debt)  # can't amortize more than debt

        debt = running_debt

        running_debt = max(0, running_debt - amort_this_year)

 

        rows.append({

            "År": year,

            "Årsavgift bostäder": arsavgift,

            "Hyra lokaler": hyra_lokaler,

            "Fastighetsskatt (vidare)": fastighetsskatt,

            "Totala intäkter": total_intakter,

            "Tomträttsavgäld": tomtratt,

            "Drift (övrigt)": drift_ovrig,

            "Övriga ext. kostnader": ovriga_ext,

            "Avskrivningar": avskrivningar,

            "Räntekostnader": ranta,

            "Skuld": debt,

            "Amortering": amort_this_year,

            "Resultat": total_intakter - total_kostnader,

        })

 

    df = pd.DataFrame(rows)

 

    # === Per sqm chart data ===

    cost_cols = ["Tomträttsavgäld", "Räntekostnader", "Drift (övrigt)", "Övriga ext. kostnader", "Avskrivningar"]

    df_chart = df[["År"] + cost_cols].copy()

    for col in cost_cols:

        df_chart[col] = df_chart[col] / TOTAL_AREA

 

    df_melted = df_chart.melt(id_vars="År", var_name="Kostnadspost", value_name="kr/m²")

 

    fig = px.bar(

        df_melted,

        x="År",

        y="kr/m²",

        color="Kostnadspost",

        title="Kostnadsfördelning per m² totalyta — staplad",

        barmode="stack",

        color_discrete_map={

            "Tomträttsavgäld": "#e74c3c",

            "Räntekostnader": "#f39c12",

            "Drift (övrigt)": "#3498db",

            "Övriga ext. kostnader": "#9b59b6",

            "Avskrivningar": "#95a5a6",

        }

    )

    fig.update_layout(xaxis=dict(dtick=1))

 

    # Income line

    fig.add_trace(go.Scatter(

        x=df["År"],

        y=df["Totala intäkter"] / TOTAL_AREA,

        mode="lines+markers",

        name="Intäkter/m²",

        line=dict(color="green", width=3),

    ))

 

    # === Apartment fee table ===

    fee_rows = []

    for _, row in df.iterrows():

        year = int(row["År"])

        avgift_per_kvm = row["Årsavgift bostäder"] / BOSTADSYTA

        for apt in apartments:

            monthly = avgift_per_kvm * apt["snitt_yta"] / 12

            fee_rows.append({

                "År": year,

                "Typ": apt["typ"],

                "Månadsavgift (kr)": round(monthly),

            })

 

    df_fees = pd.DataFrame(fee_rows)

    df_fees_pivot = df_fees.pivot(index="Typ", columns="År", values="Månadsavgift (kr)")

    df_fees_pivot.columns = [str(c) for c in df_fees_pivot.columns]

    df_fees_pivot = df_fees_pivot.loc[["1 rok", "2 rok", "3 rok", "4 rok"]]

 

    # === Loan per m² table ===

    df_loan = df[["År", "Skuld"]].copy()

    df_loan["Lån/m² (totalyta)"] = (df_loan["Skuld"] / TOTAL_AREA).round(0).astype(int)

    df_loan["Lån/m² (bostadsyta)"] = (df_loan["Skuld"] / BOSTADSYTA).round(0).astype(int)

    df_loan["År"] = df_loan["År"].astype(int)

    df_loan_display = df_loan[["År", "Skuld", "Lån/m² (totalyta)", "Lån/m² (bostadsyta)"]]

 

    # === Display ===

    mo.vstack([

        mo.md("## Kostnadsfördelning per m²"),

        fig,

        mo.md("## Månadsavgift per lägenhetstyp (kr)"),

        mo.ui.table(df_fees_pivot.reset_index()),

        mo.md("## Skuldsättning per m²"),

        mo.ui.table(df_loan_display),

        mo.md("## Resultatöversikt"),

        mo.ui.table(df[["År", "Totala intäkter", "Tomträttsavgäld", "Räntekostnader", "Skuld", "Resultat"]].round(0)),

    ])

    return

 

 

if __name__ == "__main__":

    app.run()