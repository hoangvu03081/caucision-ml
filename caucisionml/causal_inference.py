import pandas as pd
import numpy as np
from dowhy import CausalModel
from dowhy.causal_identifier.identified_estimand import IdentifiedEstimand

from econml.metalearners import XLearner
from sklearn.linear_model import LinearRegression, TweedieRegressor
from sklearn.preprocessing import OrdinalEncoder


def infer_from_project(
    df: pd.DataFrame,
    control_promotion: str,
    data_schema: dict,
    causal_graph: str,
) -> (pd.DataFrame, XLearner, OrdinalEncoder, IdentifiedEstimand, CausalModel):
    original_df = df

    categories = df["promotion"].unique()
    categories = np.delete(categories, np.argwhere(categories == control_promotion))
    categories = np.insert(categories, 0, control_promotion)

    df = df.dropna(subset=["outcome"])
    df = df.drop(columns=["user_id"])
    df["conversion"] = df["outcome"].apply(lambda x: 1 if x > 0 else 0)
    # TODO: Do we need to drop all NA columns?
    # TODO: Do we need to use OneHotEncoder, or is get_dummies enough?

    encoder = OrdinalEncoder(categories=[categories])
    encoder.fit(df[["promotion"]])
    df[["promotion"]] = encoder.transform(df[["promotion"]])

    model = CausalModel(
        data=df,
        treatment="promotion",
        outcome=["outcome", "conversion"],
        graph=causal_graph,
    )
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)

    treatment = identified_estimand.treatment_variable
    outcome = identified_estimand.outcome_variable
    estimating_instrument_names = identified_estimand.instrumental_variables

    effect_modifier_names = model._graph.get_effect_modifiers(
        identified_estimand.treatment_variable, identified_estimand.outcome_variable
    )
    observed_common_causes_names = identified_estimand.get_backdoor_variables().copy()

    w_diff_x = [
        w for w in observed_common_causes_names if w not in effect_modifier_names
    ]

    if len(w_diff_x) > 0:
        effect_modifier_names.extend(w_diff_x)
    effect_modifiers = df[effect_modifier_names]
    # TODO: Think about whether we need to use drop_first?
    effect_modifiers = pd.get_dummies(effect_modifiers)

    if observed_common_causes_names:
        observed_common_causes = df[observed_common_causes_names]
        observed_common_causes = pd.get_dummies(observed_common_causes, drop_first=True)

    if estimating_instrument_names:
        estimating_instruments = df[estimating_instrument_names]
        estimating_instruments = pd.get_dummies(estimating_instruments, drop_first=True)

    X = effect_modifiers
    W = None  # common causes/ confounders
    Z = None  # Instruments
    Y = df[outcome]
    T = df[treatment]

    if observed_common_causes_names:
        W = observed_common_causes
    if estimating_instrument_names:
        Z = estimating_instruments

    # TODO: Implement cross validation to choose best estimators
    est = XLearner(models=LinearRegression())
    est.fit(Y, T, X=X)

    user_effects = original_df[["user_id"]]
    prepared_df = original_df.drop(columns=["user_id", "promotion", "outcome"])
    prepared_df = pd.get_dummies(prepared_df[effect_modifier_names])

    for index, category in enumerate(categories[1:]):
        effect = est.effect(prepared_df, T1=index + 1)
        framed_effect = pd.DataFrame(
            effect, columns=[f"{category} outcome", f"{category} conversion"]
        )
        user_effects = pd.concat([user_effects, framed_effect], axis=1)

    return user_effects, est, encoder, identified_estimand, model
