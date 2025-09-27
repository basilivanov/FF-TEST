from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import Union
from enum import Enum

router = APIRouter(prefix="/api/v1")

class MathOperation(str, Enum):
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"

class MathRequest(BaseModel):
    operation: MathOperation
    num1: Union[int, float]
    num2: Union[int, float]

class MathResponse(BaseModel):
    operation: str
    num1: Union[int, float]
    num2: Union[int, float]
    result: Union[int, float]

@router.post("/math", response_model=MathResponse)
async def perform_math_operation(request: MathRequest):
    """
    Perform basic math operations (add, subtract, multiply, divide) on two numbers.
    
    Args:
        request: MathRequest containing operation and two numbers
        
    Returns:
        MathResponse with the operation result
        
    Raises:
        HTTPException: 400 for division by zero
    """
    num1, num2 = request.num1, request.num2
    operation = request.operation
    
    if operation == MathOperation.ADD:
        result = num1 + num2
    elif operation == MathOperation.SUBTRACT:
        result = num1 - num2
    elif operation == MathOperation.MULTIPLY:
        result = num1 * num2
    elif operation == MathOperation.DIVIDE:
        if num2 == 0:
            raise HTTPException(status_code=400, detail="Division by zero is not allowed")
        result = num1 / num2
    
    return MathResponse(
        operation=operation.value,
        num1=num1,
        num2=num2,
        result=result
    )