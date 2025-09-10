import mlflow
from mlflow.models import MetricThreshold


def validate_model(candidate_result: dict):
    thresholds = {
        'accuracy_score': MetricThreshold(
            threshold=0.8,  # accuracy should be >=0.8
            greater_is_better=True,
        ),
    }

    # Validate the candidate model against static threshold
    mlflow.validate_evaluation_results(
        candidate_result=candidate_result,
        baseline_result=None,
        validation_thresholds=thresholds,
    )
