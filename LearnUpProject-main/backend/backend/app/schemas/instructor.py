from pydantic import BaseModel, Field


class SubmitFinalGradeRequest(BaseModel):
    final_grade: str = Field(min_length=1, max_length=5)
    is_passed: bool
