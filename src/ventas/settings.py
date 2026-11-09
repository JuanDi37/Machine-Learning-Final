"""Configuración Kedro; los parámetros viven en conf/base."""

CONFIG_LOADER_ARGS = {
    "base_env": "base",
    "default_run_env": "local",
    "merge_strategy": {"parameters": "soft"},
}
