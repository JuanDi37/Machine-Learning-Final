"""Pronóstico directo multihorizonte: validación por orígenes semanales."""

import numpy as np
import optuna
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits


def scores(actual, predicted) -> dict:
    """WAPE evita dividir por días individuales de venta cero."""
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    error = predicted - actual
    denominator = np.abs(actual).sum()
    return {
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
        "wape": float(np.abs(error).sum() / denominator) if denominator else None,
        "bias": float(error.sum() / denominator) if denominator else None,
    }


def features(history: pd.Series, target: pd.Timestamp, horizon: int) -> dict:
    """Usar exclusivamente valores conocidos al origen del pronóstico."""
    values = history.to_numpy(dtype=float)
    return {
        "horizon": horizon,
        "weekday": target.dayofweek,
        "month": target.month,
        "day": target.day,
        "time": target.toordinal(),
        "last": values[-1],
        "lag_week": values[-(8 - horizon)],
        "lag_two_weeks": values[-(15 - horizon)],
        "mean_7": values[-7:].mean(),
        "mean_28": values[-28:].mean(),
        "std_7": values[-7:].std(),
        "trend": values[-7:].mean() - values[-14:-7].mean(),
    }


def training_frame(series: pd.Series, horizon: int):
    """Construir observaciones supervisadas con etiqueta disponible en entrenamiento."""
    rows, labels = [], []
    for origin in range(28, len(series)):
        history = series.iloc[:origin]
        for step in range(1, horizon + 1):
            position = origin + step - 1
            if position < len(series):
                rows.append(features(history, series.index[position], step))
                labels.append(series.iloc[position])
    return pd.DataFrame(rows), np.asarray(labels)


def predict_block(estimator, history: pd.Series, horizon: int):
    dates = pd.date_range(history.index[-1] + pd.DateOffset(days=1), periods=horizon)
    x = pd.DataFrame([features(history, day, step) for step, day in enumerate(dates, 1)])
    return np.maximum(0, estimator.predict(x))


def baseline(history: pd.Series, horizon: int):
    """Línea base estacional: repetir la última semana observada."""
    return np.asarray(history.iloc[-7:].tolist() * ((horizon + 6) // 7))[:horizon]


def _estimator(settings: dict, seed: int):
    return HistGradientBoostingRegressor(
        loss="squared_error", random_state=seed, early_stopping=False, **settings
    )


def train(daily: pd.DataFrame, params: dict):
    """Acotar paralelismo para evitar sobrecarga en series cortas."""
    with threadpool_limits(limits=params["model_threads"]):
        return _train(daily, params)


def _train(daily: pd.DataFrame, params: dict):
    """Optimizar sin tocar el holdout y comparar con la línea base al final."""
    dates = pd.to_datetime(daily.date)
    series = pd.Series(daily.revenue.to_numpy(dtype=float), index=pd.DatetimeIndex(dates))
    if not series.index.equals(pd.date_range(series.index.min(), series.index.max())):
        raise ValueError("NOTA: El modelo requiere una serie diaria ordenada y continua.")
    horizon, holdout = params["horizon"], params["holdout_days"]
    folds, minimum = params["cv_folds"], params["min_train_days"]
    if horizon != 7 or holdout % horizon or folds < 2 or minimum < 35 or params["trials"] < 1:
        raise ValueError(
            "NOTA: Se requiere horizonte 7, holdout múltiplo de 7, >=2 folds y >=35 días."
        )
    if len(series) < minimum + folds * horizon + holdout:
        raise ValueError(
            "NOTA: Historia insuficiente para entrenamiento, validación y holdout temporal."
        )
    development = series.iloc[:-holdout]
    origins = [len(development) - horizon * i for i in range(folds, 0, -1)]
    cached = []
    for origin in origins:
        history = development.iloc[:origin]
        x, y = training_frame(history, horizon)
        actual = development.iloc[origin : origin + horizon].to_numpy()
        cached.append((history, x, y, actual))

    def objective(trial):
        settings = {
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "max_iter": trial.suggest_int("max_iter", 80, 240, step=40),
            "max_leaf_nodes": trial.suggest_int("max_leaf_nodes", 3, 15),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 15, 50),
            "l2_regularization": trial.suggest_float("l2_regularization", 0.1, 30, log=True),
        }
        absolute, volume = 0.0, 0.0
        for history, x, y, actual in cached:
            estimator = _estimator(settings, params["seed"]).fit(x, y)
            predicted = predict_block(estimator, history, horizon)
            absolute += np.abs(actual - predicted).sum()
            volume += np.abs(actual).sum()
        if volume <= 0:
            raise ValueError("NOTA: Validación sin ingreso: WAPE no está definida.")
        return absolute / volume

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=params["seed"])
    )
    study.optimize(objective, n_trials=params["trials"], n_jobs=1)
    importances = []
    for history, x, y, actual in cached:
        estimator = _estimator(study.best_params, params["seed"]).fit(x, y)
        targets = pd.date_range(history.index[-1] + pd.DateOffset(days=1), periods=horizon)
        validation_x = pd.DataFrame(
            [features(history, target, step) for step, target in enumerate(targets, 1)]
        )
        importance = permutation_importance(
            estimator,
            validation_x,
            actual,
            scoring="neg_mean_absolute_error",
            n_repeats=5,
            random_state=params["seed"],
            n_jobs=1,
        )
        importances.append(importance.importances_mean)
    feature_importance = dict(zip(x.columns, np.mean(importances, axis=0).tolist(), strict=True))
    baseline_actual = np.concatenate([item[3] for item in cached])
    baseline_pred = np.concatenate([baseline(item[0], horizon) for item in cached])
    baseline_cv = scores(baseline_actual, baseline_pred)["wape"]
    cv_gate = baseline_cv > 0 and study.best_value <= baseline_cv * (
        1 - params["required_improvement"]
    )
    rows = []
    for origin in range(len(development), len(series), horizon):
        history = series.iloc[:origin]
        x, y = training_frame(history, horizon)
        estimator = _estimator(study.best_params, params["seed"]).fit(x, y)
        predicted = predict_block(estimator, history, horizon)
        naive = baseline(history, horizon)
        for step in range(horizon):
            rows.append(
                {
                    "date": series.index[origin + step],
                    "origin": history.index[-1],
                    "horizon": step + 1,
                    "actual": float(series.iloc[origin + step]),
                    "candidate": float(predicted[step]),
                    "baseline": float(naive[step]),
                }
            )
    predictions = pd.DataFrame(rows)
    candidate_score = scores(predictions.actual, predictions.candidate)
    baseline_score = scores(predictions.actual, predictions.baseline)
    holdout_gate = (
        candidate_score["wape"] is not None
        and baseline_score["wape"] is not None
        and candidate_score["wape"] <= baseline_score["wape"] * (1 - params["required_improvement"])
    )
    # La elección se congela con validación; el holdout controla la recomendación de uso.
    selected = "hist_gradient_boosting" if cv_gate else "seasonal_naive_7"
    x, y = training_frame(series, horizon)
    fitted = _estimator(study.best_params, params["seed"]).fit(x, y)
    future = predict_block(fitted, series, horizon) if cv_gate else baseline(series, horizon)
    predictions["selected"] = predictions.candidate if cv_gate else predictions.baseline
    metrics = {
        "selected_model": selected,
        "cv_candidate_wape": study.best_value,
        "cv_baseline_wape": baseline_cv,
        "cv_gate_passed": bool(cv_gate),
        "deployment_gate_passed": bool(cv_gate and holdout_gate),
        "holdout_candidate": candidate_score,
        "holdout_baseline": baseline_score,
        "holdout_selected": scores(predictions.actual, predictions.selected),
        "best_parameters": study.best_params,
        "seed": params["seed"],
        "trials": params["trials"],
        "validation_feature_importance_mae_um": feature_importance,
        "interpretation_note": (
            "NOTA: importancia por permutación calculada solo en validación; "
            "pocos días y variables correlacionadas limitan estabilidad. No es efecto causal."
        ),
        "required_improvement": params["required_improvement"],
        "holdout_start": str(series.index[-holdout].date()),
        "holdout_end": str(series.index[-1].date()),
        "protocol": (
            "Validación expansiva; holdout con actualización cada siete días; "
            "sin reajuste de hiperparámetros."
        ),
        "intervals": "NOTA: cuatro semanas no permiten validar cobertura de intervalos.",
    }
    artifact = {
        "model": fitted if cv_gate else None,
        "selected_model": selected,
        "history": series,
        "horizon": horizon,
        "metrics": metrics,
    }
    forecast = pd.DataFrame(
        {
            "date": pd.date_range(series.index[-1] + pd.DateOffset(days=1), periods=horizon),
            "prediction": future,
        }
    )
    return artifact, metrics, predictions, study.trials_dataframe(), forecast
