"""
Constants for the predictions service.
Contains all magic numbers and hardcoded values used throughout the codebase.
"""

# Dummy model prediction constants
DEFAULT_RSI_VALUE = 50.0
RSI_OVERSOLD_THRESHOLD = 30
RSI_OVERBOUGHT_THRESHOLD = 70
DEFAULT_CLOSE_PRICE = 100

# Prediction multipliers and confidence scores
PRICE_INCREASE_MULTIPLIER = 1.02  # 2% increase
PRICE_DECREASE_MULTIPLIER = 0.98  # 2% decrease
HIGH_CONFIDENCE_SCORE = 0.7
MEDIUM_CONFIDENCE_SCORE = 0.5

# Signal strength values
POSITIVE_SIGNAL_STRENGTH = 0.5
NEGATIVE_SIGNAL_STRENGTH = -0.5
NEUTRAL_SIGNAL_STRENGTH = 0.0

# Dummy model metadata
DUMMY_MODEL_NAME = 'dummy_rsi_model'
DUMMY_MODEL_VERSION = '1.0.0'
DEFAULT_PREDICTION_HORIZON_MINUTES = 5

# Model features
DUMMY_MODEL_FEATURES = ['rsi_14', 'close']
DEFAULT_PREDICTION_TYPE = 'price_direction'

# Exit codes
ERROR_EXIT_CODE = 1

# Validation field names
REQUIRED_INDICATOR_FIELDS = ['pair', 'close',
                             'window_start_ms', 'window_end_ms']

# Time constants
HOURS_IN_DAY = 24
MINUTES_IN_HOUR = 60
SECONDS_IN_MINUTE = 60
MILLISECONDS_IN_SECOND = 1000

# Training constants
DEFAULT_TRAIN_TEST_SPLIT = 0.8
MIN_SPLIT_RATIO = 0.1
MAX_SPLIT_RATIO = 0.9
MIN_PERCENTAGE_MISSING_VALUES = 0.0
MAX_PERCENTAGE_MISSING_VALUES = 1.0
DEFAULT_HYPERPARAM_TRIALS = 5
DEFAULT_HYPERPARAM_SPLITS = 3

# Port ranges
MIN_PORT = 1
MAX_PORT = 65535

# Model validation constants
MIN_ACCURACY_THRESHOLD = 0.8
DEFAULT_MAX_PERCENTAGE_DIFF_MAE = 0.50

# Schema version
PREDICTION_SCHEMA_VERSION = "1.0"

# Hyperparameter tuning ranges for HuberRegressor
HUBER_EPSILON_MIN = 1.0
HUBER_EPSILON_MAX = 99999999
HUBER_ALPHA_MIN = 0.01
HUBER_ALPHA_MAX = 1.0
HUBER_MAX_ITER_MIN = 100
HUBER_MAX_ITER_MAX = 1000
HUBER_TOL_MIN = 1e-4
HUBER_TOL_MAX = 1e-2
