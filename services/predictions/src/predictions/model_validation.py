import mlflow
from mlflow.models import MetricThreshold
from predictions.constants import MIN_ACCURACY_THRESHOLD


def validate_model(candidate_result: dict) -> None:
    thresholds = {
        'accuracy_score': MetricThreshold(
            threshold=MIN_ACCURACY_THRESHOLD,  # accuracy should be >=0.8
            greater_is_better=True,
        ),
    }

    # Validate the candidate model against static threshold
    mlflow.validate_evaluation_results(
        candidate_result=candidate_result,
        baseline_result=None,
        validation_thresholds=thresholds,
    )
