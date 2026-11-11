from dataclasses import dataclass
from uuid import UUID

from app.modules.training.workout_schemas import WorkoutContent


@dataclass(frozen=True)
class ValidatedGeneration:
    execution_id: UUID
    content: WorkoutContent
    base_id: UUID | None
    explanation: str
