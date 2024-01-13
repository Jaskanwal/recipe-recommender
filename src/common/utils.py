import unicodedata
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

# function to remove non-ascii characters from a string
clean_non_ascii = (
    lambda string: unicodedata.normalize("NFKD", string)
    .encode("ascii", "ignore")
    .decode("utf-8")
    .strip(" ")
)


def get_pre_process_pipeline(
    temp_columns,
    temp_pca_n_components,
    model,
    model_name="model",
    one_hot_categorical=False,
    categorical_features=[],
    numerical_untransformed_features=[],
):
    transformer_list = [
        (
            "temp_pipeline",
            Pipeline(
                [
                    ("select_cols_temp", DataFrameSelector(temp_columns)),
                    ("pre_scalar", StandardScaler()),
                    (
                        "pca",
                        pca_with_get_feature_names_out(
                            n_components=temp_pca_n_components
                        ),
                    ),
                    ("post_scalar", StandardScaler()),
                ]
            ),
        )
    ]

    if len(categorical_features) > 0:
        if one_hot_categorical:
            transformer_list.append(
                (
                    "cat_pipeline",
                    Pipeline(
                        [
                            (
                                "select_cols_cat",
                                DataFrameSelector(categorical_features),
                            ),
                            (
                                "encoder",
                                OneHotEncoder(
                                    handle_unknown="ignore",
                                    drop="first",
                                    sparse_output=False,
                                ),
                            ),
                        ]
                    ),
                )
            )
        else:
            transformer_list.append(
                (
                    "cat_pipeline",
                    Pipeline(
                        [("select_cols_cat", DataFrameSelector(categorical_features))]
                    ),
                )
            )

    if len(numerical_untransformed_features) > 0:
        transformer_list.append(
            (
                "numeric_untransformed_pipeline",
                Pipeline(
                    [
                        (
                            "select_cols_num",
                            DataFrameSelector(numerical_untransformed_features),
                        )
                    ]
                ),
            )
        )

    pre_process_pipeline = FeatureUnion(transformer_list)

    analysis_pipeline = Pipeline(
        [("pre_process_pipeline", pre_process_pipeline), (model_name, model)]
    )

    return analysis_pipeline
