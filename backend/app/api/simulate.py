"""Simulation / demo endpoints for testing without real data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.simulate import (
    SimulateFullDay, SimulateStressSpike, SimulateWeightTrend,
    SimulateMealLog, SimulateWorkoutComplete, SimulationResponse,
)
from app.api.deps import get_current_user
from app.services.simulation_service import (
    simulate_full_day, simulate_stress_spike, simulate_weight_trend,
    simulate_meal_log, simulate_workout_complete, reset_simulation_data,
)

router = APIRouter(prefix="/simulate", tags=["Simulation"])


@router.post("/full-day", response_model=SimulationResponse)
def sim_full_day(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = simulate_full_day(user, db)
    return SimulationResponse(simulation_type="full_day", data=result)


@router.post("/stress-spike", response_model=SimulationResponse)
def sim_stress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = simulate_stress_spike(user, db)
    return SimulationResponse(simulation_type="stress_spike", data=result)


@router.post("/weight-trend", response_model=SimulationResponse)
def sim_weight(body: SimulateWeightTrend, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    result = simulate_weight_trend(user, db, direction=body.direction, days=body.days)
    return SimulationResponse(simulation_type=f"weight_{body.direction}", data=result)


@router.post("/meal-log", response_model=SimulationResponse)
def sim_meal(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = simulate_meal_log(user, db)
    return SimulationResponse(simulation_type="meal_log", data=result)


@router.post("/workout-complete", response_model=SimulationResponse)
def sim_workout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = simulate_workout_complete(user, db)
    return SimulationResponse(simulation_type="workout_complete", data=result)


@router.post("/reset")
def sim_reset(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = reset_simulation_data(user.id, db)
    return {"message": "Simulation data reset", "deleted": result}
