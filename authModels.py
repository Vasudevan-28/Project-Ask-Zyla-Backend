from pydantic import BaseModel

class SaveUserModel(BaseModel):
    name: str
    email: str
    phone: str
    firebase_uid: str
    password: str   
    created_at: str


class SignUpModel(BaseModel):
    name: str
    email: str
    dob: str
    gender: str
    city: str
    state: str
    country: str
    timezone: str
    skin_profile: bool
    phone: str
    password: str
    firebase_uid: str


class LoginModel(BaseModel):
    identifier: str   # email or phone
    password: str


class EmailRequest(BaseModel):
    email: str


class PhoneRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: int


class ResetPasswordPhone(BaseModel):
    phone: str
    new_password: str


class ResetPasswordEmail(BaseModel):
    # email: str
    new_password: str    
    
class ForgotPasswordEmail(BaseModel):
    email : str
    new_password : str
    
class SetNewPassword(BaseModel):
    new_password: str


class EmailOtpVerify(BaseModel):
    email: str
    otp: int


class PhoneOtpAttempt(BaseModel):
    phone: str


class SaveToken(BaseModel):
    email: str
    fcm_token: str


class GoogleEmailCheck(BaseModel):
    email: str


