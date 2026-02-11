from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    def validate_password_length(cls, v):
        if len(v) < 4:
            raise ValueError('Пароль должен быть не менее 4 символов')
        return v
    
class UserLogin(BaseModel):
    email: str
    password: str
    
class ResumeCreate(BaseModel):
    content: str
    
class MatchRequest(BaseModel):
    resume_id: int
    vacancy_id: int