"""Basic fraud/outlier detection for leaderboard and lifestyle points."""
import logging

logger = logging.getLogger(__name__)

STEP_DAILY_MAX = 80_000
WORKOUT_DAILY_MAX = 5
WATER_DAILY_MAX = 10_000  # ml
CALORIE_DAILY_MAX = 8_000


def check_steps(steps: int) -> bool:
    if steps > STEP_DAILY_MAX:
        logger.warning(f"Suspicious step count: {steps}")
        return False
    return True


def check_workout_count(count: int) -> bool:
    if count > WORKOUT_DAILY_MAX:
        logger.warning(f"Suspicious workout count: {count}")
        return False
    return True


def check_water_intake(ml: float) -> bool:
    if ml > WATER_DAILY_MAX:
        logger.warning(f"Suspicious water intake: {ml}ml")
        return False
    return True


def check_calorie_intake(cal: float) -> bool:
    if cal > CALORIE_DAILY_MAX:
        logger.warning(f"Suspicious calorie intake: {cal}")
        return False
    return True


def should_flag_leaderboard(steps: int = 0, workouts: int = 0, water_ml: float = 0, calories: float = 0) -> bool:
    return steps > STEP_DAILY_MAX * 7 or workouts > WORKOUT_DAILY_MAX * 7
