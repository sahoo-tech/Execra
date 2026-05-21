from fastapi import APIRouter
from core.hybrid.alert_suppressor import alert_suppressor 
router = APIRouter()

@router.get("/suppression/stats")
def get_suppression_stats()-> dict:
    return alert_suppressor.get_suppression_stats()